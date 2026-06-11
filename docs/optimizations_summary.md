# Optimisations — résumé rapide

Benchmark : rendu de 300 frames en 1080p avec 47 glyphes de texte animés
(`python3 test/perf/bench.py`). Détails complets dans
[optimization.md](optimization.md).

| | Avant | Après | Gain |
|---|---|---|---|
| Chargement (lancement → 1ʳᵉ frame) | 2,06 s | 0,56 s | **3,7×** |
| Vitesse de rendu | 17,0 ms/frame | 9,5 ms/frame | **1,8×** |
| Rendu total | 7,17 s | 3,42 s | **2,1×** |
| RAM max | 686 Mo | 461 Mo | **−33 %** |

### 1. Copy-on-write des arguments de métadonnées

Chaque input transportait ses arguments de création sous forme d'objet JSON
(un glyphe de texte est un contour d'environ 600 points), copié en profondeur
une fois par frame et par input — au chargement puis à chaque frame rendue ;
le profiling a montré que ce brassage de JSON était le premier coût CPU,
devant tout le travail graphique réel. L'objet est désormais derrière un
`shared_ptr` : copier une métadonnée n'est plus qu'une incrémentation de
compteur de références, et seul le rare shader qui modifie réellement les
arguments les clone avant écriture (copy-on-write).

### 2. Index de lecture sorti du JSON

Le numéro de frame courant était écrit *dans* cet objet JSON à chaque frame
(`args["index"] = i`), ce qui forçait une copie profonde de l'objet entier
alors que seuls les inputs vidéo le lisent. C'est maintenant un simple champ
entier de la métadonnée : plus rien ne touche au JSON sur le chemin
par-frame.

### 3. Transfert des meshes sans copie

Le core renvoyait la liste complète des meshes — chaque vertex de chaque
forme — par valeur à chaque frame, et le chargeur de timeline copiait le JSON
de chaque entrée trois fois lors de l'ingestion. La liste de meshes est
désormais renvoyée par référence vers le cache interne, et les entrées de
timeline sont déplacées (move) au lieu d'être copiées.

### 4. Encodage en pipeline

Le renderer écrivait chaque frame brute de 8,3 Mo dans le pipe FFmpeg avec un
`fwrite` bloquant : tout le programme attendait pendant que x264 compressait
(~21 % du temps par frame). Un thread d'écriture dédié, derrière une petite
file bornée, alimente maintenant FFmpeg : la frame N est encodée pendant que
la frame N+1 est construite et rendue.

### 5. Imports Python paresseux

`import videocode` payait ~50 ms pour `shapely` (qui entraîne numpy) alors
qu'il n'est utilisé que par une seule méthode de hit-testing, et les scènes
d'échecs payaient ~100 ms pour `python-chess` qui calcule ses tables d'attaque
à l'import. Les deux sont désormais importés à la première utilisation, ce qui
fait passer `import videocode` de 112 ms à 60 ms.

### Correctif annexe : `make verbose`

Le Makefile passait `-DVC_VERBOSE=ON` à CMake mais rien ne le consommait : le
chronométrage des phases de démarrage intégré au code était inatteignable
quelle que soit la build. Il est maintenant câblé — c'est ainsi qu'ont été
mesurés les chiffres de chargement ci-dessus (la phase d'ingestion de la
timeline est passée à elle seule de ~1,9 s à 61 ms, soit ~30×).

### Vérification

Les 19 tests de régression visuelle passent, et une frame prise au milieu de
la vidéo du benchmark est identique au pixel près (différence moyenne 0,0) au
rendu d'avant optimisation. Les pistes d'optimisation futures sont listées
dans `wherewasi`.

## Optimisations antérieures (historique git)

| Commit | Optimisation | Gain mesuré |
|---|---|---|
| `c193918` | Génération en flux — les frames sont rendues et encodées au fil de l'eau au lieu d'être toutes générées au départ | La vidéo entière n'est plus gardée en RAM |
| `d6dc8ee` | Échantillonnage des glyphes `_STEPS` 12 → 4 (~1800 → ~600 pts/lettre) ; exécution de la scène in-process via pybind11 embed (plus de sous-processus `popen`, plus d'aller-retour JSON) | Chargement de scène ~700 ms → ~445 ms |
| `00169ba` | `perf: O11+O12` — copie de shader évitée pour les shaders sans effet (autodestroy avant copie) ; cache de géométrie C++ par input dans `BezierPath` (buildPath + earcut sautés quand la géométrie n'a pas changé) | Exec Python 0,954 s → 0,298 s (−69 %) ; construction du mesh d'une lettre 1500–2000 µs → 500–700 µs/frame |
| `ba727eb` | Hot-reload incrémental — le diff de la stack saute entièrement les inputs inchangés et réutilise les objets existants (`resetModifications`), conservant les caches mesh/GPU et évitant les relectures disque Image/Video à chaque édition | L'édition-rechargement ne reconstruit plus toute la scène |
