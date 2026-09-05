# Features à faire

Document de travail. `FEATURES.md` dit ce que le projet sait faire ; celui-ci dit
ce qu'il ne sait pas encore, ce qui est cassé, et dans quel ordre s'y prendre.

Issu de cinq passes de recherche sur le dépôt (2026-09-03). Chaque entrée porte
un identifiant stable : dis « fais X3 » ou « fais B1 » et il n'y a pas
d'ambiguïté. Les tailles sont des ordres de grandeur, pas des engagements.

La vue courte de ce document est un tableau tenu à jour en direct :
**https://claude.ai/code/artifact/a80200f9-2f71-48e8-b59e-7a8d6353e3ca** — source
dans `docs/board.html`, règles de mise à jour dans `CLAUDE.md`. Ce fichier-ci est
la trace : les mesures, les chiffres, les conceptions écartées et pourquoi.

Trois règles qui reviennent partout dans ce document :

- **Une image de référence ne se réécrit que quand un humain l'a regardée.**
  C'est ce qui bloque X3, et c'est pour ça que plusieurs corrections attendent.
- **L'empreinte du corpus (50 scènes) doit rester inchangée**, sauf décision
  explicite. C'est la barrière qui a attrapé trois erreurs cette nuit.
- **Un défaut qui répond faux en silence vaut plus qu'une commodité manquante.**
  Sept des huit corrections livrées cette nuit étaient de cette famille.

---

## 1. Les défauts mesurés

Rangés par le moment où quelqu'un les rencontre. Tous vérifiés en exécutant le
cas, pas déduits.

| # | Ce qui casse | Rencontré | Coût | Bloqué par |
|---|---|---|---|---|
| **X1** | **Fait — `b309d23`.** `docs/user/user.md`, la page liée depuis le README, enseignait `from videocode.VideoCode import *`, `video(...)` et `.add()` — aucun des trois n'existe. `docs/by-example/firstRectangle.py` faisait 0 octet. Le README ne mentionnait jamais `--editor`. Chaque extrait a été exécuté avant d'être écrit : `apply(grayscale())` seul ne dure qu'une image (chroma 0,523 mesurée à l'image 20, identique au clip brut), la page dit donc `duration=1`. Les douze pages `docs/user/inputs/*.md` et `transformation/*.md` enseignent la même API morte ; elles sont dé-liées, pas réécrites | Première minute | 1 h | — |
| **X2** | **Fait — voir le commit.** `Image("x.png")` sans dimension ne produisait aucune géométrie côté Python : la grouper ou l'encadrer plantait. Le cas nu lit maintenant la taille naturelle du fichier, comme le faisait déjà la branche `cornerRadius`. Aucun golden réécrit : les six passent la tolérance de la suite — écart maximal **1/255** sur une centaine de pixels sur deux millions, et `image_shape` est identique au pixel. Seule l'empreinte bouge (`chess`, `image_shape`, 0 → 8 points par image) | Première photo | ½ j | — |
| **X3** | **Fait — `71013d9`.** Chaque instant écrit après un `wait()` coûtait une image : `wait(1); Circle(); wait(1)` = 61 images, dix étapes = 340 au lieu de 330. Un curseur (`Context.cursor`) distinct de la fin exclusive ; `wait()` et `timestamp()` le lisent. Deux scènes du digest bougent (`chess` 133→131, `silk` 31→30), aucun golden : l'image 130 de `chess` existe toujours et est identique au pixel | Chaque scène | ½ j | — |
| **X4** | **Fait — `8ad1f9c`.** Un nombre ne peut plus remplacer qu'un nombre. Un nom ou une expression est refusé à voix haute, en le nommant ; et depuis B7 le refus propose la seule modification permise — celle de la constante elle-même. L'éditeur remplace une constante nommée par un littéral : glisser sur `wait(PAUSE_DELAY)` écrit `wait(0.5)` et efface le nom. Le tutoriel fait ça à 30 endroits. La fiche refuse déjà ce cas, le glissement non | Premier glissement | 1 h | — |
| **X5** | **Fait — `8ad1f9c`.** Le modèle porte le fichier sur l'élément, sur chaque effet et sur chaque point d'insertion ; un geste sur une ligne d'un autre fichier nomme ce fichier et s'arrête. Le correctif `0b8e060` a rebranché la ligne du modèle vers la barre, sans quoi le garde-fou lisait `undefined` et laissait tout passer. Un geste sur un élément défini dans un autre fichier écrit dans le tampon de la scène, à ce numéro de ligne — donc **réécrit une ligne au hasard** | Multi-fichiers | 1 h | — |
| **X6** | **Fait — `7dabb14`.** `Polygon.width` et `Group.width` ignoraient `meta.scale` : `Square(2).scale(2)` était mesuré 2 alors qu'il en dessine 4. Polygon, Rectangle, RightTriangle et CompoundPolygon lisent ET écrivent la taille dessinée ; `Text` garde la géométrie pour sa propre mise en page. Une scène bouge, et c'est le but : le pivot de `stateful_group_scale` passe du centre des boîtes non mises à l'échelle au centre de ce qui est dessiné. Deux goldens régénérés après les avoir regardés côte à côte | Premier `nextTo` | ½ j | — |
| **X7** | **Fait — `e1ad561`.** Le son propre d'une vidéo n'était jamais monté (`buildAudioArgs` ne collectait que les `Sound`). Il suit maintenant l'horloge de l'image : départ à 0, mêmes plages coupées (`asplit`/`atrim`/`concat` — `aselect` ne coupe rien sur ffmpeg 8.0.1, mesuré), `atempo` quand la source n'est pas à 30 fps. Mesuré sur un clip muet une seconde puis tonalité : `startFrame=30` laisse 1,005 s de son sans aucun silence ; `cuts=[(15, 45)]` finit le silence à 0,500 ; une scène avec un `Sound` seul monte la même commande qu'avant (silence_end 2,000045 avant et après). Pas porté au son : speed ramps, `freeze()`, source > 60 fps | Premier export parlant | 1 h | — |

X4 et X5 sont des heures et ne bloquent rien. X2, X3 et X6 sont la
condition d'autres features (X6 porte D1, D2, D6).

---

## 2. Le verrou structurel

### S1 — Résolution différée de la base · 2 semaines · 0 C++

Aujourd'hui une animation lit sa valeur de départ **au moment où la ligne est
exécutée** (`moveTo.py:24` : `src = v2(*input.meta.position)`), pas au moment où
elle joue. Juste tant que les lignes sont écrites dans l'ordre du film,
silencieusement faux sinon. `Context.backdatedWrites()` existe pour en avertir,
et son propre commentaire dit que le vrai remède « demanderait que chaque ligne
ait tourné d'abord ».

**Ce qui a été écarté après conception :** écrire un *marqueur* à la place de la
valeur, résolu après coup. Ça ne marche que pour cinq canaux (déplacer, grandir,
tourner, estomper, aligner) : dix-neuf autres modèles font de la trigonométrie
ou des divisions sur cette base. Un marqueur ne survit pas à un cosinus.

**Ce qui tient :** exécuter la scène **deux fois**. La première donne la vérité
image par image ; si un décalage est détecté, la seconde rejoue en donnant à
chaque animation sa base réelle, lue dans le résultat de la première. ~40 lignes,
aucun modèle réécrit, rien à toucher en C++.

Mesuré sur prototype :

| | |
|---|---|
| Scènes du corpus où la deuxième passe se déclenche | **0 / 50** |
| Scènes qui bougent avec la deuxième passe forcée | **0 / 50** |
| Idem sans la règle « même image » (voir ci-dessous) | 4 / 50 |

La règle « même image » : quand une animation ouvre sur l'image où l'objet vient
d'être placé, sa base est ce placement, pas l'image d'avant. Quatre scènes du
corpus font exactement ça à l'image zéro.

**Ce que ça corrige :** `moveTo(x=5, start=2)` puis `moveTo(x=2)` donne
aujourd'hui 4,99 → 2 selon l'ordre d'écriture ; après, le même film dans les
deux ordres.

**Ce que ça ne corrige pas :** un `Group` compose sur sa position cumulée, qui
n'existe nulle part dans la pile — aucune conception ne peut lui donner une
base. Un décalage au niveau du groupe reste invisible, y compris à
l'avertissement.

**Livrable sans drapeau** : aucune scène ne déclenche la deuxième passe, donc la
barrière du corpus prouve elle-même que rien ne bouge.

**La preuve à écrire** — pas « la suite passe » : inverser les deux lignes de
`test/contention_test.py:162-166` et exiger que les deux ordres donnent le même
film, et qu'une chaîne de `moveBy` inversée finisse à 3.0 (aujourd'hui 2.0).

**S1 commande D7, B4, A3 et B3.** Ces quatre-là sont faux sans lui.

---

## 3. Les concepts

Taille : **S** une après-midi · **M** quelques jours à une semaine · **L** un
projet.

### A — Moteur et langage de scène

| # | Ce que c'est | Taille | Dépend de |
|---|---|---|---|
| **A1** | **Comp** — un groupe qui se rend comme **un seul calque** : sa propre transformation, son opacité, ses effets, son masque. Corrige d'un coup les groupes imbriqués qui perdent l'animation intérieure, le fondu de groupe où les membres se traversent, et le masque qui exige d'aplatir un texte à la main. Le moteur a déjà les couches isolées et la passe qui aplatit une plage de maillages | L | — |
| **A2** | **Caméra** — déplacer et zoomer l'image entière. Un uniforme dans l'étage sommet, **pas** un composite de tout. Demande un `pinToFrame()` pour ce qui ne doit pas zoomer (sous-titres) | M | — |
| **A3** | **Valeur suivie + liaison** — un nombre qui évolue, des objets qui le lisent. `attachTo` est déjà la moitié écriture, `Group._ownPositions` la moitié lecture ; il manque le verbe général | M | S1 |
| **A4** | ~~Flou de mouvement~~ — **écarté**, voir §5 | — | — |
| **A5** | **`moveAlong(path)`** — parcourir une courbe, tourné dans le sens de la marche. Presque tout existe : il manque l'échantillonnage par longueur d'arc | S | A3 |
| **A6** | **Fait — `4c66575`.** `over().volume` était revendiqué sur la timeline et jeté au montage. Le graphe audio lit maintenant le niveau image par image (une expression `volume` posée APRÈS `adelay`, donc dans l'horloge de la scène), et `duck(under=)` écrit les deux rampes du geste. Mesuré sur deux rendus du même son : 0,20 après une rampe vers 0,2, et 1,00 retrouvé après la voix. **Le son sur le modèle de revendications** — `music.over(duration=1.5).volume = 0`, et `music.duck(under=voice)` | M | X7 |
| **A7** | **Fait — `0b05a91`.** `--from` / `--to`, en secondes ou par nom de `timestamp()` ; au-delà de la fin, on borne. Les délais audio n'ont pas été décalés : la timeline entière est mixée comme avant et l'extrait est découpé du résultat (un `atrim`), ce qui vaut pour `Sound` et pour la piste d'une `Video` d'un coup. Mesuré : un son à 8 s est à 5,5 s d'un rendu `--from 2.5`, et déjà en cours à 0 d'un `--from 9` | S | — |

### B — L'atelier

| # | Ce que c'est | Taille | Dépend de |
|---|---|---|---|
| **B1** | **Fait — `406b110`.** La ligne du curseur allume la barre qu'elle fabrique — l'animation gagne sur la déclaration — et ⌘⏎ joue depuis ce moment. Mesuré : la barre du cercle passe de 124 à 135 de vert quand le curseur entre dans sa ligne, celle du carré ne bouge pas. A demandé de réparer le harnais d'abord (`fa0fe1e`) : la fenêtre sans écran ne recevait aucune touche. **Le curseur de texte est une tête de lecture** — la ligne où tu es allume sa barre ; une touche joue depuis là. Aucune écriture, que de la lecture | S | — |
| **B2** | ~~Glissement sur les nombres~~ — **écarté**, voir §5 | — | — |
| **B3** | **Glisser vs décaler** — tirer le corps d'un clip écrit son `.wait()`, tirer le bord d'une bande rouge écrit le `wait()` global. Les deux outils de Premiere sont deux mots du langage. Demande un `insertLinkSpan` dans `edit.py` | M | S1 (vers la gauche) |
| **B4** | **Fiche chronomètre** — la valeur de l'élément **à la tête de lecture**, et en taper une autre écrit l'animation qui y mène. Doit refuser d'écrire dans une fenêtre déjà revendiquée | M | S1 |
| **B5** | **Fait — `38315e3`.** Une pastille de courbe au bout de chaque ligne d'effet, un panneau de 200 px avec deux points tirables et les presets, et l'écriture au relâchement seulement. `CubicBezier` existait déjà dans la librairie mais n'était pas dans l'espace de noms d'une scène — c'était ça, le trou. **Éditeur de courbes** — une courbe tirable sur chaque effet, qui écrit `easing=CubicBezier(...)`. Les presets et les courbes à main sont déjà le même type | M | — |
| **B6** | **Fait — `775459a`.** La règle prend une deuxième rangée seulement si la scène a nommé quelque chose ; ⇧←/⇧→ sautent d'un repère à l'autre et disent le nom. **Les repères** — `timestamp()` est écrit 30 fois dans le tutoriel et n'est **jamais dessiné**. Le C++ sait déjà sauter de l'un à l'autre. Il manque trois lignes dans `sceneModel` | S | — |
| **B7** | **Fait — `3fbfc71`.** Le refus est devenu le bouton : « PAUSE_DELAY → 0.9, lu sur 3 lignes · clique pour le changer », et un clic change la ligne de la constante et rien d'autre. Une barre fabriquée par une boucle porte « ×3 ». **Ce qu'un geste doit refuser** — badge « ×3 » sur un clip fait dans une boucle, refus sur un autre fichier (X5), et l'inverse constructif : si l'argument est une constante nommée, proposer de changer **la constante** | S puis M | X4, X5 |

### C — Sortie, agent, réutilisation

| # | Ce que c'est | Taille | Dépend de |
|---|---|---|---|
| **C1** | **Fait — `9c9e743`.** `--sheet N` pose N moments côte à côte dans une seule image, chaque vignette étant exactement l'image que `--from` aurait écrite, avec son temps dans une bande dessous. Refusé sur une sortie vidéo. **L'agent regarde l'image qu'il vient de faire** — il modifie, rend la frame (9 ms, sans fenêtre), l'ouvre, et dit que le titre déborde. Demande `--frame N` / `--at 1.5`, et une planche-contact `--sheet` | S | A7 |
| **C2** | **Fait — `212197c`.** Cinq lignes devant chaque question — fichier, ligne du curseur, élément sélectionné avec ses effets, tête de lecture, dernier run et ses avertissements — plus `--inspect`, qui imprime le modèle de scène en JSON. **L'agent sait où tu es** — aujourd'hui il ne reçoit **que ton texte** : ni le fichier, ni ta ligne, ni la sélection, ni la tête de lecture, ni les avertissements du dernier run. Plus un `--inspect` qui imprime le modèle de scène en JSON | S | — |
| **C3** | **Fait — `98d4dec`.** `--for youtube,tiktok,square` écrit un fichier par forme en rejouant la scène à chaque fois : mesuré, le marqueur est à 0,26 en travers en 16:9 et à 0,26 en hauteur en 9:16 — une remise en page, pas un recadrage. La normalisation de loudness est laissée de côté, elle changerait le son de tous les rendus existants en silence. **Une scène, tous les formats** — `--for youtube,tiktok,square`. La scène **se remet en page** (`setScreen`, `Split.AUTO`) au lieu d'être recadrée. Plus la normalisation de loudness | M | — |
| **C4** | **Fait — `c628a96`.** Fichier → Export Video… (⌘E, plus un bouton dans la barre de transport) lance le même binaire que la ligne de commande, respecte les repères d'entrée/sortie, et affiche le compte d'images du moteur lui-même. Ce qui est rendu est le TAMPON, copié à côté de la scène pour que les chemins relatifs tiennent. **Exporter depuis l'éditeur** — un bouton, une barre de progression, la plage entre les repères. L'éditeur ne sait aujourd'hui **pas exporter du tout**. La décision est déjà écrite dans `BACKLOG.md` : même binaire, progression lue sur la sortie | M | A7 |
| **C5** | **Fait — `0b82b06`.** La découverte marchait déjà ; ce qui manquait, c'est ce qui rate — un modèle qui ne s'importe pas disparaissait sans un mot. Il s'affiche maintenant en rouge avec sa raison, non cliquable. **Tes propres modèles** — un dossier `templates/` dans ton projet, découvert dans le panneau avec ses champs. La machinerie existe, elle ne regarde que le paquet de la librairie | S | — |
| **C6** | **Fait — `dd53e52`.** Chaque `timestamp()` devient un chapitre du conteneur et une ligne à coller sous la vidéo. Un rendu `--from` les décale avec lui. Et quand la liste enfreint une des trois règles de YouTube, le rendu le dit — une liste que YouTube ignore en silence est exactement ce que cet outil ne doit pas rendre. **Chapitres et miniature** — chaque `timestamp()` devient un chapitre dans le fichier et une ligne à coller sur YouTube | S | B6, C1 |
| **C7** | ~~Montage par transcription~~ — **écarté**, voir §5 | — | — |

### D — Le langage

Faits comptés sur le corpus : `strokeColor=TRANSPARENT` **89 fois** (le contour
par défaut est ce que personne ne veut) · **18** tailles de police distinctes ·
**27** variables dans le tutoriel créées seulement pour regrouper et faire
disparaître plus tard · **13** `.opacity(0)` avant un fondu d'entrée.

| # | Ce que c'est | Taille | Dépend de |
|---|---|---|---|
| **D1** | **`b.nextTo(a, UP, gap=0.2)`** — mettre ceci à côté de cela. Avec `follow=True`, ça suit quand l'autre bouge (relecture par image, comme `_ownPositions`) | S puis M | X6 ; S1 pour `follow` |
| **D2** | **Fait — `76ae86a`.** **`Row` / `Column` / `Grid`** (`videocode/template/input/Layout.py`) — `gap` mesuré bord à bord, centré même en nombre pair, `align=start/center/end`, `Grid(cols=, rowGap=, colGap=)`, imbrication par le contenu (`Group._anchorOf`). `XAlign`/`XStack`/`YStack` intacts, digest inchangé. Limite connue : `Text.width` somme l'encre des glyphes (1,10 pour « hello » contre 1,44 de boîte réelle), donc un Text en Row est mesuré court ; et tant que X6 n'est pas accepté, un membre mis à l'échelle est mesuré sans son échelle | S | X6 (pour les membres mis à l'échelle) |
| **D3** | **`with shot() as intro:` + `cut(intro, body, crossfade)`** — nommer un plan, couper vers le suivant. Tue le motif des 27 variables | M | A1 pour un vrai fondu |
| **D4** | ~~`theme()`~~ — **écarté**, voir §5 | — | — |
| **D5** | **`stagger(popIn(), every=0.08)`** — la même entrée un temps après l'autre. Trois implémentations câblées en dur existent déjà (`typewriter`, `Text.typeIn`, `Graph`) ; c'est leur généralisation, ~15 lignes | **S** | — |
| **D6** | **`BarChart(data)` / `Leaderboard(rows)`** — un élément par ligne de données, `fromCSV` inclus. Remplace 12 à 15 lignes dont la valeur affichée qui ne suit pas la barre | M | D1, D2, D5 |
| **D7** | **`at=2.5`** — dire *quand* en secondes. Cinq lignes de sucre, mais **aggrave** le piège de la base tant que S1 n'est pas fait | S | **S1** |

---

## 4. Trois routes

Chacune est un travail cohérent, pas une liste de courses.

**Bureau — 2,5 semaines.** *Pour* : éditer une scène avec l'agent à côté. À la
fin, la ligne du curseur s'allume, l'agent rend et regarde ce qu'il vient
d'écrire, on exporte une plage depuis la fenêtre, et aucun geste ne réécrit la
mauvaise chose.
Ordre : X1, X4, X5, X7 → A7 → C1 → C2 → B1 → B6 → C4 → C5 → B7 → B5.
Laisse de côté : tout ce qui écrit du temps à rebours.

**Faite, le 5 septembre 2026.** Les douze sont livrées et attendent d'être
regardées à la main. Deux trous d'outillage trouvés en chemin et bouchés : la
fenêtre sans écran ne recevait aucune touche (`fa0fe1e`), et le harnais
photographiait avant la fin des touches — donc tout raccourci « vérifié » avant
ce jour ne l'était pas. Reste ouvert : un `Shortcut` de fenêtre (espace, I, O)
ne part toujours pas dans un run scripté, même par la couche plateforme ; la
moitié transport du clavier se relit, elle ne se déclenche pas.

**Temps — 6 semaines.** *Pour* : écrire des scènes qui disent *quand* et *par
rapport à quoi*.
Ordre : X2, X3, X6 → **S1** → D7 → A3 → D1 → D2 → D5 → B4 → B3 → D6.
Laisse de côté : le compositing et la livraison.

**Plan — 5 semaines.** *Pour* : faire une **vidéo** et non une scène. Les deux
autres routes ne donnent jamais le moyen de commencer un second plan sans que le
premier déborde.
Ordre : A1 → D3 → A2 → X7 + A6 → C6 → C3.
Laisse de côté : la liaison par image et l'atelier.

**Trois mois, dans l'ordre :** semaine 1 les défauts et la doc · semaines 2-3
Bureau · semaines 4-5 S1 · semaines 6-8 le reste de Temps · semaines 9-11 Plan ·
semaine 12 B5 et du mou.

---

## 5. Écartés, et pourquoi

- **A4 — Flou de mouvement.** Le moteur n'a **aucune donnée entre les images** :
  sa table est par image entière. Un flou déduit des images voisines est un
  maquillage sur des formes nettes dessinées au code. Manim n'en a pas, pour la
  même raison.
- **C7 — Montage par transcription.** Un modèle de transcription, une interface
  par mots, et `cuts=` existe déjà sur `Video`. C'est un autre produit sous le
  même nom.
- **B2 — Glissement sur les nombres dans le code.** Une semaine pour un geste
  qui ne marche que sur un littéral — et le code refuse justement d'écrire des
  littéraux là où l'auteur a mis une expression. B4 et le glissement sur la
  timeline couvrent l'intention.
- **D4 — `theme()`.** C'est un fichier de constantes et un `import`. Le
  construire ajoute une couche de résolution sans nouvelle capacité.
- **A2 fait comme un composite de tout.** Garder A2, mais comme un uniforme.
