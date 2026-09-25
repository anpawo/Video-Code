# Objectif 1 — Ouvrir le projet : périmètre et licence

Livrables de la séance de septembre du track Technique (guide Tech 5, p. 3 et 6).
Mentor : Quentin Forand. Séance de cadrage tenue le 17/09/2026.

## 1. Périmètre : tout le projet est ouvert

**Décision : le dépôt entier est public** — `github.com/anpawo/Video-Code`, branche `main`,
moteur C++/Vulkan, bibliothèque Python, éditeur QML, tests, docs, CI. Aucun composant n'est
isolé, rien n'est gardé dans un dépôt privé.

Pourquoi tout, et pas un composant :

- Le produit *est* la bibliothèque. Un développeur qui écrit une scène a besoin du moteur
  qui la rend ; en ouvrir une moitié ne donnerait rien d'utilisable à personne.
- Ce qu'on veut garder n'est pas du code, c'est un droit : l'usage commercial de l'outil.
  C'est la licence qui le garde (section 2), pas un dépôt fermé.
- Un dépôt unique est le seul que les trois membres et la CI savent maintenir.

Ce qui reste hors du dépôt : les clés de signature macOS et le miroir de déploiement
(`cd-mirror.yaml` pousse par git nu, sans action tierce) ; aucun secret dans l'historique.

## 2. Licence : PolyForm Noncommercial 1.0.0 + deux permissions

Fichier : `LICENSE` (SPDX `PolyForm-Noncommercial-1.0.0`), texte PolyForm intact, deux permissions ajoutées au-dessus, commits `af6e673` → `0b4b62b`
(22–23/09/2026). Résumé dans `README.md` § License.

| Quelqu'un veut… | Réponse |
|---|---|
| Lire, cloner, modifier, redistribuer le code pour un usage personnel, éducatif, recherche, associatif | **Oui** (PolyForm NC) |
| Publier une vidéo faite avec Video-Code, y compris monétisée (pub, sponsor, cours payant) | **Oui**, à condition du crédit « made with mariusrousset.com/videocode » — 30 jours pour le remettre s'il manque (permission 1) |
| Garder ses scènes, templates et le code écrit par un agent IA sous sa propre licence, les vendre | **Oui**, le projet n'y réclame rien (permission 2) |
| Produire une vidéo sur commande payée par un client | **Non sans accord** écrit préalable |
| Intégrer Video-Code dans un produit ou service commercial (SaaS, plugin vendu, studio) | **Non** — c'est ce que la clause non commerciale interdit |
| Retirer la notice ou redistribuer sans les termes | **Non** (section Notices de PolyForm) |

Pourquoi ce texte et pas un autre :

- **Pas MIT/Apache** : elles autoriseraient un tiers à vendre l'outil tel quel. Le projet
  vise un modèle semi-ouvert (`docs/FEATURES_TODO.md` n° 60) où l'outil reste gratuit pour
  les créateurs et l'exploitation commerciale se négocie.
- **Pas GPL/AGPL** : le copyleft ne bloque pas le commercial, il impose seulement d'ouvrir ;
  et il aurait contaminé les scènes des utilisateurs, ce que la permission 2 refuse
  explicitement.
- **Pas un texte maison** : le brouillon VCL-1.1 a été abandonné pour un texte connu et
  déjà lu par les juristes ; les spécificités tiennent dans deux permissions courtes.
- Conséquence assumée : **ce n'est pas « open source » au sens de l'OSI** (la clause non
  commerciale l'exclut). Le mot juste est *source ouverte, usage non commercial*.

## 3. Compatibilité des dépendances

Toutes les dépendances sont permissives ou LGPL ; aucune n'impose sa licence au projet.
Vérifié le 25/09/2026 sur `vcpkg.json` et `requirements.txt`.

| Dépendance | Version | Licence | Compatible ? |
|---|---|---|---|
| Qt (qtbase, qtdeclarative) | 6.11.1 | LGPL-3.0 | Oui, **voir point de vigilance** |
| FFmpeg | 8.1.2 | LGPL-2.1+ (build vcpkg sans feature `gpl`) | Oui, **voir point de vigilance** |
| OpenCV | 4.12.0 | Apache-2.0 | Oui |
| Vulkan headers / loader, MoltenVK | 1.4.350 | Apache-2.0 | Oui |
| glslang | 16.3.0 | BSD-3 / Apache-2.0 / MIT ; la partie GPL-3 est le parser Bison, exception Bison | Oui |
| FreeType | 2.14.3 | FTL (BSD-like) | Oui |
| protobuf | 6.33.4 | BSD-3-Clause | Oui |
| curl | 8.20.0 | curl (MIT-like) | Oui |
| argparse, nlohmann-json, earcut-hpp, miniaudio | — | MIT / MIT / ISC / MIT-0 | Oui |
| shapely, freetype-py, pygments | — | BSD | Oui |
| Pillow, svgelements, pyright/basedpyright | — | MIT-CMU / MIT / MIT | Oui |
| uharfbuzz | 0.54.1 | Apache-2.0 | Oui |
| typing_extensions | 4.15.0 | PSF-2.0 | Oui |
| Police Inter (`assets/fonts`) | — | SIL OFL 1.1 | Oui, licence jointe |

Retiré pour incompatibilité : **python-chess (GPL-3.0)** — le template `chessboard`, sa scène,
ses goldens et les 13 PNG de chess.com sont sortis du dépôt le 18/09/2026. Une dépendance GPL
aurait obligé à distribuer l'outil sous GPL, incompatible avec la clause non commerciale.

**Point de vigilance — LGPL en lien statique.** Les triplets vcpkg lient tout en statique
(`VCPKG_LIBRARY_LINKAGE static`, macOS et Linux). La LGPL le permet, mais exige qu'un
utilisateur du binaire distribué (`dist/video-code-macos-arm64.zip`) puisse **remplacer Qt et
FFmpeg par sa propre version** : soit fournir les fichiers objets du projet pour rééditer les
liens, soit passer ces deux bibliothèques en dynamique. Rien de tout cela n'est fait aujourd'hui.
À traiter avant la prochaine release publique ; le plus simple est le lien dynamique pour Qt et
FFmpeg seulement.

## 4. Qui possède ce qui est publié

- Le crédit exigé pointe sur `mariusrousset.com/videocode`, adresse portée par le README pour
  pouvoir changer sans casser les vidéos déjà publiées.
- **Contributions externes** : le projet n'a pas encore de `CONTRIBUTING.md` ni d'accord de
  contributeur. Sans lui, chaque contribution externe reste la propriété de son auteur et
  interdit de relicencier plus tard. À écrire avant les appels à contributions de novembre :
  le contributeur garde son copyright et accorde une licence irrévocable avec droit de
  relicencier (modèle Qt, déjà tranché au n° 60).

## 5. Ce qui manque encore pour cet objectif

| Livrable (guide p. 6) | Échéance | État |
|---|---|---|
| Note de périmètre | séance de septembre | ce document |
| Licence + analyse + dépendances | séance de septembre | ce document ; lien LGPL à régler |
| Doc landing / installation / contribution | fin octobre | README et `docs/readme/` existent ; `CONTRIBUTING.md` absent |
| Test de reproductibilité par un tiers, daté | fin octobre | à faire |
| 5 issues ouvertes dont 3 « good first issue » | fin octobre | 34 issues ouvertes, aucune étiquette *good first issue* |
| 5 appels à contributions, journal daté | nov.–déc. | à faire |
| Gouvernance, roadmap publique, plan post-EIP | fin décembre | à faire |
