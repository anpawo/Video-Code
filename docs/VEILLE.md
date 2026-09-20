# Veille — outils regardés, et ce qu'on en fait

Un outil regardé de près coûte une demi-journée. Le regarder deux fois coûte
une deuxième demi-journée pour rien. Ce fichier garde le verdict *et* la
raison, comme la colonne « Won't do » du tableau de bord.

Trois verdicts possibles : **adopter**, **ignorer**, **à creuser**.

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

*Écrit le 2026-09-20. Tout ce qui est chiffré ici a été mesuré ce jour-là ;
la cadence de publication d'HyperFrames, en particulier, vieillira vite.*
