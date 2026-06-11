# Rapport d'optimisation

Benchmark reproductible : `python3 test/perf/bench.py` (rend
`test/perf/stress_text.py` — 47 polygones de lettres animés, 300 frames en
1080p, ~13 800 entrées de timeline — puis exécute la suite de régression
visuelle). Machine : Apple Silicon, macOS, build release (`make cmake`).

## Résultats

| | Chargement (lancement → 1ʳᵉ frame) | Rendu | Total | RAM max | Suite de tests |
|---|---|---|---|---|---|
| **Avant** (11/06/2026) | 2,06 s | 17,0 ms/frame | 7,17 s | 686 Mo | 5,5 s |
| **Après** (11/06/2026) | **0,56 s** | **9,5 ms/frame** | **3,42 s** | **461 Mo** | 5,8 s |
| Gain | **3,7×** | **1,8×** | **2,1×** | −33 % | — |

Détail par phase (build verbose, `make verbose`) : `executeStack` — la passe
C++ qui ingère la timeline Python — est passée de ~1,9 s à **61 ms (~30×)**.
Exactitude : les 19 tests de régression visuelle passent, et une frame prise
au milieu de la vidéo du benchmark est identique au pixel près (différence
moyenne 0,0) au rendu d'avant optimisation. La RAM restante vient
essentiellement des buffers de l'encodeur x264 et de l'interpréteur Python
embarqué, pas de notre code.

## Ce qui était lent (cause racine)

Le profiling (`sample` macOS sur le binaire release + `cProfile` sur la couche
Python) a montré que le renderer passait l'essentiel de son temps CPU à
**copier et libérer du JSON**, pas à faire du graphisme :

- La `Metadata` de chaque input transporte ses arguments de création complets
  sous forme d'objet `nlohmann::json` — pour un glyphe de texte, c'est un
  contour d'environ 600 points, soit plus de 1500 nœuds JSON alloués sur le
  tas.
- Cet objet était **copié en profondeur une fois par frame et par input** au
  chargement (`AInput::add` remplit `_metas` densément, une `Metadata`
  complète par frame) et **à nouveau à chaque frame rendue**
  (`AInput::getMetadata` renvoyait par valeur, et `meta.args["index"] = frame`
  forçait la mutation/copie).
- La boucle de frames était entièrement séquentielle : construction des
  meshes (CPU) → rendu et attente du GPU → copie des pixels → `fwrite`
  bloquant de 8,3 Mo dans le pipe FFmpeg. Chaque étape restait inactive
  pendant que les autres travaillaient.

## Optimisations nommées

1. **Copy-on-write des arguments de métadonnées** (`Metadata.hpp`,
   `AInput.cpp`, `IVertexShader.hpp`) — `Metadata::argsPtr` est un
   `std::shared_ptr<const json::object_t>` au lieu d'un objet JSON par valeur.
   Copier une `Metadata` n'est plus qu'une incrémentation de compteur de
   références ; seul le rare vertex shader `Args` clone l'objet avant de le
   modifier (copy-on-write classique). Ce seul changement a fait passer le
   chargement de 2,06 s à 0,61 s et supprimé ~6 ms/frame de brassage JSON
   dans la boucle de rendu — et il rend la timeline `_metas` dense (une
   entrée par frame) assez bon marché pour qu'aucune restructuration en
   keyframes creuses ne soit nécessaire.
2. **Index de lecture sorti du JSON** (`Metadata::frameIndex`) — l'index de
   lecture vidéo par frame était stocké *dans* le JSON des arguments
   (`args["index"] = i`), forçant une copie modifiable de l'objet entier à
   chaque frame pour chaque input. C'est maintenant un simple champ entier ;
   seul `Video` le lit.
3. **Transfert des meshes sans copie** — `Core::generateMeshes()` renvoie une
   `const std::vector<Mesh>&` vers les meshes en cache au lieu de copier
   chaque vertex de chaque mesh une fois par frame ; l'ingestion de la
   timeline (`Core::rebuildInput` → `AInput::add`) déplace (move) le JSON des
   arguments au lieu de le copier trois fois par entrée.
4. **Encodage en pipeline** (`Compiler.cpp`) — le `fwrite` des frames brutes
   dans le pipe FFmpeg s'exécute sur un thread d'écriture dédié derrière une
   file bornée à 4 frames : la frame N est encodée par x264 pendant que la
   frame N+1 est construite et rendue (c'était ~21 % de la boucle de frames,
   entièrement séquentiel).
5. **Imports Python paresseux** — `shapely` (qui entraîne numpy) n'est
   importé que lorsque `Polygon.contains()` est appelé, et `python-chess`
   (~100 ms de calcul de tables d'attaque à l'import) que lorsqu'un
   `ChessBoard` est construit. `import videocode` : 112 ms → 60 ms.

Correctif annexe : `make verbose` (`-DVC_VERBOSE`) est désormais réellement
câblé dans CMake — il ne définissait rien auparavant — ce qui active le
chronométrage `[startup]` des phases, utilisé pour mesurer les temps de
chargement.
