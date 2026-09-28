# Veille — outils regardés, et ce qu'on en fait

Un outil regardé de près coûte une demi-journée. Le regarder deux fois coûte
une deuxième demi-journée pour rien. Ce fichier garde le verdict *et* la
raison, comme la colonne « Won't do » du tableau de bord.

Trois verdicts possibles : **adopter**, **ignorer**, **à creuser**.

Quatre outils regardés le 2026-09-20 : HyperFrames, l'API Higgsfield, Palmier
Pro, Remotion. Aucun adopté. Ce qui en sort tient en deux lignes de tableau
(66, 67) et une idée vue deux fois — voir Remotion.

---

## HyperFrames — ignorer comme dépendance, garder deux idées

`github.com/heygen-com/hyperframes`, Apache-2.0, par HeyGen. Une composition
est du HTML : chaque clip est un élément avec `data-start`, `data-duration`,
`data-track-index`. Le rendu cherche chaque image dans un Chrome headless et
encode le résultat avec FFmpeg.

**Pourquoi pas.** C'est l'architecture que video-code a déjà écartée. Le moteur
ici est Vulkan ; une image coûte des millisecondes, pas un aller-retour dans un
navigateur. Et ce qu'HyperFrames apporte vraiment — *la composition est un
document déclaratif qu'une IA peut éditer sans se tromper* — video-code l'a
déjà, en mieux : le document est un fichier Python, la timeline le lit, l'agent
l'édite avec Read/Edit. On ne va pas remplacer un fichier de code par du HTML.

**En plus, c'est trop jeune pour qu'on s'y attache** (mesuré le 2026-09-20) :

| | |
|---|---|
| Versions publiées depuis le 2026-03-23 | 409 |
| Cadence des 7 derniers jours | 3 par jour |
| `@hyperframes/core`, `@hyperframes/engine` | publiés **sans licence** |
| Dépendances de la CLI | 17 |

Seul le paquet `hyperframes` porte Apache-2.0 ; les deux paquets qu'on
importerait réellement n'annoncent aucune licence sur npm. À trois versions par
jour, épingler une version c'est épingler un bug, et suivre c'est un travail à
plein temps.

**Les deux idées à voler, elles, sont bonnes :**

- **« Prêt » ≠ « la durée est connue ».** Leur `compositionReadiness.ts` ne
  capture une image qu'une fois que *chaque ressource déclarée* est stabilisée :
  vidéos sous `readyState < HAVE_FUTURE_DATA`, images `!complete`, polices en
  `fonts.status === "loading"` — avec un `AbortSignal` qui coupe l'attente dès
  que la course est finie et un plafond à 8 s. **Non vérifié chez nous** : est-ce
  que `--generate` peut rendre une image d'une vidéo pas encore décodée ? La
  question vaut d'être posée avant d'écrire quoi que ce soit.
- **`hyperframes lint`** : une passe de vérification sur la composition
  elle-même, avant de rendre quoi que ce soit. L'équivalent chez nous serait un
  `--lint` qui dit « ce clip commence après la fin de la scène », « ce `wait()`
  est négatif », « cet élément n'est jamais visible » — sans rendre une image.
  Moins cher qu'un golden, et ça attrape une autre classe d'erreurs.

---

## API Higgsfield — ignorer

`POST https://api.higgsfield.ai/higgsfield-ai/soul/v2/standard`, en-tête
`Authorization: Key <id>:<secret>`. Asynchrone : la requête rend un
`request_id`, on interroge ensuite ou on écoute un webhook. Un endpoint
`/estimate/...` chiffre avant de dépenser (`{"credits":"1.500","usd":"0.094"}`).
Paiement à l'usage, recharge minimum 5 $, crédits périmés au bout d'un an ;
une génération ratée ou refusée pour NSFW n'est pas facturée.

**Pourquoi pas.** Ce n'est pas le même métier. video-code est déterministe : le
même fichier rend la même image, c'est ce qui rend les goldens et le digest de
bake possibles. Une API de génération rend une image différente à chaque appel —
elle ne peut être *source* d'un média, jamais *étape* d'un rendu. Et il faudrait
créer un compte payant, ce qui n'est pas à moi de faire.

**Ce qu'on garde quand même :** la forme de l'API est triviale (REST + polling,
une cinquantaine de lignes), et le détail qui vaut d'être copié, si un jour un
`generate()` entre dans le projet, c'est **l'endpoint d'estimation** : on peut
afficher le prix à l'auteur avant qu'il appuie, pas après.

---

## Palmier Pro — à creuser (sa liste d'outils, pas son code)

`palmier-io/palmier-pro`, Swift, 14 439 étoiles. GPL-3.0 pour les sources
jusqu'à la v0.7.6, binaires propriétaires ensuite. Serveur MCP sur
`http://127.0.0.1:19789/mcp`, **sans authentification**.

**Pourquoi on n'adopte rien.** C'est une app macOS en Swift, fermée depuis la
v0.7.6, avec un serveur MCP ouvert sans jeton sur la machine. Rien à importer.

**Pourquoi ça vaut quand même le détour.** Ses 49 outils MCP sont un cahier des
charges gratuit : la liste de ce qu'une IA doit savoir faire sur un montage,
écrite par des gens qui s'y sont cassé les dents avant nous.

```
manage_project get_timeline inspect_timeline create_timeline set_active_timeline
manage_markers set_project_settings export_project manage_exports get_media
inspect_media search_media import_media capture_frame organize_media manage_tracks
manage_clip_links add_clips insert_clips move_clips remove_clips split_clips
ripple_delete_ranges swap_clip_media set_clip_properties copy_clip_settings
set_keyframes apply_layout sync_clips undo manage_multicam change_cam get_multicam
get_transcript remove_words remove_silence detect_beats add_texts update_text
add_captions apply_color apply_effect inspect_color denoise_audio list_models
generate_video generate_image generate_audio upscale_media send_feedback
read_skill manage_skills
```

**Le premier enseignement est rassurant.** Il leur faut 49 outils là où il nous
en faut quatre, et c'est une conséquence de l'architecture, pas un retard :
chez eux le montage est un état binaire opaque dans une app, donc chaque geste
doit devenir un outil. Chez nous le montage est un fichier texte, donc
`add_clips`, `insert_clips`, `move_clips`, `remove_clips`, `split_clips`,
`swap_clip_media`, `set_clip_properties`, `copy_clip_settings`, `add_texts`,
`update_text`, `set_keyframes`, `manage_tracks`, `undo` — treize outils —
tiennent dans `Edit` plus `git`. **Le nombre d'outils n'est pas une cible à
rattraper.** Ce qu'on a déjà en face du reste :

| Chez eux | Chez nous |
|---|---|
| `get_timeline`, `inspect_timeline` | `--inspect --file <scene>` (JSON, un objet par élément) |
| `capture_frame` | `--generate look.png --from 2.5`, et `--sheet 4` |
| `manage_markers`, état de l'éditeur | `tell state`, `tell seek` |
| `export_project`, `manage_exports` | le rendu lui-même |

**Le vrai manque est ailleurs, et il est réel.** Ce qui ne se déduit *pas* du
fichier de scène, parce que ça demande de regarder le média :
`get_transcript`, `remove_silence`, `detect_beats`, `add_captions`,
`inspect_color`, `denoise_audio`, `upscale_media`. Un agent qui édite du code ne
peut pas savoir où sont les silences ni sur quel temps tombe la musique. C'est
la seule case de leur catalogue qu'on ne coche pas.

Mais la moitié de cette case est déjà refusée, et à raison : **le montage par
transcription est en « Won't do » depuis le 17 sept.** (ligne 42 du tableau, *«
autre produit »*). `get_transcript`, `remove_silence` et `add_captions` sont
exactement ça — les revoir chez un concurrent ne change pas l'argument.

**Il ne reste donc qu'une piste, et elle est étroite : `detect_beats`.** Caler
une animation sur la musique, c'est du timing, pas du montage parlé — c'est le
métier de l'outil. Et ça reste une analyse hors-ligne qui rend une liste de
nombres, donc des `timestamp()` de plus dans le fichier de scène : aucune
architecture nouvelle, aucune dépendance dans le moteur.

---

## Remotion — ne pas importer son code, mais prendre son principe

`remotion-dev/remotion`, 59 854 étoiles, une version tous les deux ou trois
jours depuis 2021, zéro dépendance sur le paquet principal. De loin le plus
mûr des quatre, et le plus proche de nous par l'intention.

### Le principe, en une phrase

**Une vidéo est une fonction pure du numéro d'image vers une image.** Tout le
reste en découle :

- `useCurrentFrame()` est la *seule* source du temps. Pas d'horloge murale, pas
  d'état accumulé.
- `<Sequence from={30}>` ne déplace rien : il **décale le numéro d'image que
  ses enfants reçoivent**. Composer dans le temps, c'est renommer l'entrée, pas
  muter une timeline.
- Parce que c'est pur, ils rendent les images **en parallèle dans plusieurs
  onglets indépendants**. C'est le gain, et c'est pour ça que le principe est
  tenu si strictement.
- L'impôt à payer, écrit noir sur blanc dans leur page « flickering » : un
  composant doit donner le même visuel à chaque appel, ne pas dépendre de
  l'ordre de rendu, ne pas s'animer en pause, et ne pas tirer au hasard.
- `delayRender()` / `continueRender()` / `cancelRender()` sont la seule façon
  légale de n'être « pas prêt » : la fonction dit qu'elle ne peut pas encore
  répondre, au lieu de répondre faux.

### Ce que ça dit de notre architecture — et c'est plutôt bon

Chez nous la scène est un programme Python **exécuté une seule fois**, de haut
en bas, qui empile des statements ; `wait()` avance un curseur ; les images
sont ensuite rendues depuis ce résultat cuit. Impératif-puis-cuit, là où
Remotion est pur-par-image.

Conséquence : **toute la classe de bugs de leur page « flickering » ne peut pas
nous arriver.** La scène ne tourne jamais par image, donc deux fils ne peuvent
pas diverger. Leurs quatre règles sont l'impôt de React et du rendu parallèle,
pas une loi universelle. Et leur `<Sequence>` — décaler le temps vu par un
sous-arbre — on l'a déjà : `offset=` et `at=` dans `apply()`.

### Le seul endroit où leur leçon nous vise vraiment

Ils ont dû inventer `random(seed)` parce que `Math.random()` casse le rendu.
Chez nous, vérifié le 2026-09-20 : **aucun tirage au hasard nulle part** —
zéro `random` dans `videocode/`, dans les scènes, dans les templates, et
aucune graine posée. On est déterministe *par absence*, pas par conception.

Le jour où une scène éparpille des particules avec `random.uniform()`, elle
sera cohérente dans une exécution (la scène ne tourne qu'une fois) mais
**différente à la suivante** : les goldens se mettent à battre, et l'empreinte
des 54 scènes — la barrière que `CLAUDE.md` désigne comme celle qui a attrapé
ce que toutes les autres laissaient passer — commence à mentir. Une barrière
qui bat finit désactivée.

Ça ne demande pas de code aujourd'hui (personne n'en a besoin), mais ça demande
de le savoir avant d'en avoir besoin. Ligne 69 du tableau.

### Et la licence, correctement lue

Elle n'est pas OSI (`SEE LICENSE IN LICENSE.md`, `NOASSERTION` côté API). Ce
qu'elle interdit est précis : « copy or modify Remotion code **for the purpose
of selling, renting, licensing, relicensing, or sublicensing your own derivate
of Remotion** ». Donc :

| | |
|---|---|
| L'utiliser, même commercialement | **permis** — la Free License couvre un individu, et video-code n'est pas une société |
| Lire son code, comprendre son modèle, réimplémenter l'idée | **permis** — le droit d'auteur protège l'expression, pas l'idée |
| Copier son code dans un outil vidéo qu'on licencie ensuite | **interdit**, et c'est ce que serait video-code le jour où la ligne 60 aboutit |

Son modèle de licence à seuil (gratuit jusqu'à 3 salariés) avait déjà été
examiné pour *notre* licence par le council du 17 sept. et écarté : pas de
société pour facturer, et le seuil tombe mal. Noté ici pour que la question ne
soit pas rouverte une troisième fois.

**Donc :** on n'importe pas son code — l'architecture ne nous va pas de toute
façon, React rendu image par image dans un Chrome headless quand on a un moteur
Vulkan. Mais c'est le projet à lire quand on se demande à quoi ressemble une
bonne API de vidéo-par-le-code, et il a confirmé deux choses : l'idée de
« readiness » vue une deuxième fois, et `freeze` en verbe de premier rang, ce
qui appuie la ligne 53.

---

*Écrit le 2026-09-20. Tout ce qui est chiffré ici a été mesuré ce jour-là ;
la cadence de publication d'HyperFrames, en particulier, vieillira vite.*

---

## Un lecteur à nous — ne pas faire un lecteur, faire ce qui est branché sur video-code

Regardé le 2026-09-28, parce qu'Aperçu n'anime pas un GIF (il en montre les
images comme des pages ; QuickTime refuse le GIF, le WebM et le MKV — testés).
Verdict : **ignorer** le lecteur généraliste, **à creuser** les trois choses
que personne ne fait. Ligne 79 du tableau.

**Déjà fait, gratuit, inutile à refaire :**

| Besoin | Outil | Licence |
|---|---|---|
| Tout lire (GIF, WebM, MKV), image suivante/précédente, boucle A-B, vitesse | IINA | GPL-3, appli séparée |
| Numéro d'image, zoom sans lissage, pipette, comparer deux vidéos (côte à côte, volet, différence) | mrv2 | BSD-3 |
| Volet à la souris sur deux vidéos synchronisées, différence en couleurs, scores | video-compare (`brew install video-compare`) | GPL-2, programme séparé |
| Voir un GIF sans rien installer | Quick Look (espace dans le Finder), ou `ffplay -loop 0 x.gif` | — |

Les chapitres sont déjà là : le moteur écrit les `timestamp()` comme chapitres
du MP4, et IINA ou mpv les lisent.

**Ce que personne ne fait** (non trouvé — une absence ne se prouve pas) :

- **L'image vers les lignes Python qui la dessinent**, surlignées pendant la
  lecture. Motion Canvas et Remotion ne vont que d'un élément à la ligne qui
  l'a créé, et en JS.
- **Comparer deux vidéos et trancher le golden** — accepter réécrit la
  référence. Ça existe pour des captures fixes (BackstopJS, Argos, Chromatic),
  pas pour la vidéo, ni dans un lecteur.
- **Le contrôle avant envoi dans une seule vue** : sonie contre une cible,
  zones des applis, noirs et silences marqués sur la timeline — aujourd'hui
  trois ou quatre outils (Resolve, LosslessCut, safezone, QC Buddy), et aucun
  ne remonte d'un défaut au code.

**Les chiffres à ne pas inventer :**

- « −14 LUFS YouTube » n'est pas officiel : YouTube, TikTok et Instagram ne
  publient rien ; le chiffre vient d'un article de 2018. Officiels : Spotify
  −14 LUFS (pic −1 dBTP), Apple Podcasts −16 LKFS. La cible sera un réglage.
- Zones : Meta Reels 14 % en haut, 35 % en bas, 6 % de chaque côté ; le calque
  vertical de Google (1080×1920) réserve 288 px en haut, 672 en bas, 48 à
  gauche, 192 à droite. Le « 10/25/10 » qui circule pour Shorts le contredit.

**Ce qu'on réutiliserait :** le FFmpeg déjà dans `vcpkg_installed` (LGPL, à
lier en dynamique et sans x264/x265) lit tout et mesure sonie, noirs, silences,
images figées, PSNR et SSIM. Le lecteur OpenCV actuel saute à l'image exacte
sur nos MP4 (62 sur 62) mais n'ouvre ni WebM ni MKV, et d'un GIF ne lit que la
première image ; le passer sur FFmpeg changerait le décodeur, donc peut-être
les goldens et l'empreinte. QtAVPlayer (MIT) est un lecteur Qt/QML sur FFmpeg,
sans port vcpkg. mrv2/tlRender (BSD-3) sont le code de comparaison à lire.

**À éviter :** libmpv (GPL par défaut, OpenGL seulement), Qt Multimedia (pas de
pas à pas ni d'arrière), QMovie (un saut non séquentiel échoue sur un GIF),
libVLC (l'image précédente attend la 4.0), GStreamer (lourd, sortie OpenGL).

Sources principales : github.com/ggarra13/mrv2, github.com/pixop/video-compare,
iina.io, support.apple.com/guide/preview/view-an-animated-gifs-frames-prvw1016/mac,
motioncanvas.io/docs/time-events/, remotion.dev/elements/overlays/social-safe-zones,
github.com/reelsmith/safezone, github.com/bavc/qctools,
support.spotify.com/us/artists/article/loudness-normalization/,
facebook.com/business/ads-guide/update/image/instagram-reels,
github.com/valbok/QtAVPlayer.

## Reference reels for the videos to make — shortlist of 2026-09-27

Eight Instagram reels kept as references for the videos made with video-code, ranked.
Nothing to build from them yet.

**Caveats.** The summaries come from captions and transcripts: nobody has watched the reels.
Authors were resolved with yt-dlp on 2026-09-27, but one link opened in a browser showed
unrelated adult content instead of the Darkvex reel: treat every link as unverified in a
browser, and never open one in a window to check it. The full set tagged video-code (9 more
reels, 5 YouTube videos) is in `~/self/reels-analysis/projects/video-code.md` and
`~/self/reels-analysis/graph.jsonl`.

| # | What it shows | Reels (author) |
|---|---|---|
| 1 | Opus 5.5 makes motion design by writing code (Three.js / Canvas / WebGL, SVG / CSS / React) that a renderer then plays — the same approach as video-code. The viral showreel comes from a multi-step pipeline, not a single prompt. | [DdvsUg_ziaX](https://www.instagram.com/reel/DdvsUg_ziaX/) (Darkvex AI) · [DdxE5CERFVd](https://www.instagram.com/reel/DdxE5CERFVd/) (Nawras Kader) · [DdwCXaQIHNU](https://www.instagram.com/reel/DdwCXaQIHNU/) (Grafigator) |
| 2 | HyperFrames, HeyGen's open-source video agent: the closest open-source project to compare against (see the HyperFrames section above). | [Ddb8HEiCifJ](https://www.instagram.com/reel/Ddb8HEiCifJ/) (Sebastian Hardy — a carousel of 5 AI news items, HyperFrames is one) |
| 3 | Palmier Pro, a macOS editor whose MCP server lets Claude Code edit the timeline (see the Palmier Pro section above). | [DaO2cHXJJUP](https://www.instagram.com/reel/DaO2cHXJJUP/) (Brody, brodyautomates) |
| 4 | Transitions to reproduce: film burn, mask glitch, flash, hand over the lens, whip pan; plus three simple motion-design transitions. | [Da0d8suu6kJ](https://www.instagram.com/reel/Da0d8suu6kJ/) (Anderson Tai) · [Dcq_NcWvW-K](https://www.instagram.com/reel/Dcq_NcWvW-K/) (François Deverre) |
| 5 | A 6-step process for scripting content (Stanley app): for choosing what the videos are about. | [DdXDuy6BNOS](https://www.instagram.com/reel/DdXDuy6BNOS/) (Nick Tarmossin) |
