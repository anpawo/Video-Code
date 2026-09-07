# Synthèse du président — le son de l'aperçu

Conseil llm-council, 5 sièges (2 Fable, 3 Opus), réponses indépendantes puis
relecture croisée anonyme. Mapping dans review/mapping.json.

## Ce que les cinq disent, sans exception
- **Pré-mixer un WAV avec la chaîne ffmpeg du rendu** (`buildAudioArgs`,
  `volumeExpression`, `videoAudioChain`, `amix normalize=0`), sortie du
  namespace anonyme de `Compiler.cpp` vers `AudioMix`. Un seul mixeur : ce
  qu'on entend est ce qu'on exporte. Le digest des 52 scènes ne bouge pas.
- **L'audio est l'horloge maître** dès qu'il y a du son ; l'image saute des
  images, jamais le son. Sans son, le compteur d'images actuel reste.
- **Pas de qtmultimedia** (rebuild vcpkg statique + plugins, pour un lecteur
  qu'un header donne).
- Pas de son au scrub ni à vitesse ≠ 1 cette nuit, dit à voix haute.

## Arbitrages après relecture
| Point | Décision | Pourquoi |
|---|---|---|
| Lecteur | **miniaudio** (port vcpkg 0.11, header-only) | un seul code mac + Linux, curseur à l'échantillon ; AVFoundation abandonnait Linux et `currentTime` est une estimation |
| WAV | décodé **en RAM**, **un nom par révision**, l'ancien supprimé | ffmpeg réécrit sinon le fichier sous le lecteur |
| Horloge | **remplacer le corps du tick** existant | deux objets qui bougent `playhead` se disputent la fin de plage |
| Indices d'entrée | paramètre `firstInput` (0 à l'aperçu, 1 au rendu) | pas d'entrée `nullsrc` factice |
| Label de sortie | **`outLabel`**, jamais `[aout]` en dur | une piste seule sort en `a0` |
| Seek | un seul `app.seekTo(t)` | Home/End/±1 image et `PreviewPanel.onSeek` bougent la tête sans couper la lecture |
| Cache | **aucun** cette nuit | `executeScene` ne tourne qu'à ⌘R / ouverture / agent, et la clé coûterait ce qu'elle évite (`ffprobe` par Video, images × entrées) |

## Ce que les cinq avaient raté, retenu
- **La panne doit parler** : `ffmpeg` résolu explicitement (une app lancée du
  Dock n'a pas `/opt/homebrew/bin` dans son PATH), et chaque raison de silence
  dite dans la barre d'état — sinon on livre le bug d'aujourd'hui avec 250
  lignes de plus.
- **Latence Bluetooth** : 150 à 250 ms sur des AirPods, 5 à 8 images ; un
  décalage réglable (`ponytail`), défaut 0.
- **Mute / volume d'aperçu** : `normalize=0` laisse clipper volontairement.
- Le curseur miniaudio n'avance pas à l'instant du `start` : garder
  `playhead` tant que le curseur est derrière.
- `Math.round` dans `PreviewPanel.qml:78` contre `floor` à l'export.

## Preuve
Sans fenêtre : le PCM du WAV d'aperçu est identique (md5) à la piste audio de
`--generate` pour une scène à deux `Sound` + duck ET une scène à un seul
`Sound`. Puis `--check-chrome`. Puis une écoute humaine.

## Marche à suivre
1. `AudioMix.{hpp,cpp}` : déplacement pur + `firstInput` + graphe/format
   séparés. Digest inchangé, export d'une scène à son identique à l'octet.
2. `vcpkg.json` + miniaudio ; `Speaker` (load/play/pause/seek/position/mute).
3. `Editor::bakeAudio()` après `sceneBuilt()` : QProcess ffmpeg résolu, WAV
   par révision, échec annoncé, rien en headless.
4. QML : `seekTo()` unique ; tick = curseur audio quand il y en a un ;
   `onPlayingChanged` → play/pause.
5. Test PCM aperçu == export, une et deux pistes.
6. Dire à Marius ce qui change : images sautées sous pane lente, pas de son
   au scrub, pas de vitesse.
