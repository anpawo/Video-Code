# Siège 2 — le son de l'aperçu

**Recommandation ferme : WAV pré-mixé par la chaîne ffmpeg du rendu, joué par miniaudio, et l'audio devient l'horloge maître de la tête de lecture. Pas de qtmultimedia.**

## Pourquoi pas qtmultimedia
- Rebuild vcpkg de Qt statique : des heures, pour un `QMediaPlayer` dont le seek est grossier et dont l'horloge n'est pas lisible à l'échantillon près. `QAudioSink` obligerait de toute façon à décoder le WAV soi-même.
- `miniaudio` est dans les ports vcpkg (vérifié dans `~/.cache/vcpkg`), header-only, CoreAudio sur mac et PulseAudio/ALSA sur Linux avec le même code. Coût : une ligne dans `vcpkg.json`, un `find_path` dans `CMakeLists.txt`, aucun rebuild de Qt.
- `AVAudioPlayer` en `.mm` ferait 40 lignes sur mac (OBJCXX déjà activé pour `MetalSurface.mm`) mais rien sur Linux : deux chemins pour une nuit, non.

## Chemin de la nuit (4 étapes, ~250 lignes, 5 fichiers)
1. **`src/compiler/Compiler.cpp` + `Compiler.hpp`** — sortir `buildAudioArgs` de l'anonyme avec un paramètre `firstInput` (aujourd'hui `tracks + 1` suppose le rawvideo en entrée 0 ; défaut 1 → la commande de mux reste identique à l'octet, le digest des 50 scènes ne bouge pas) et ne pas émettre `-map 0:v` quand `firstInput == 0`. Ajouter `std::string premixCommand(inputs, frames, wav)` = `ffmpeg -y {inputs} -filter_complex "…" -map "[aout]" -ar 48000 -ac 2 -c:a pcm_s16le {wav}`. Le codec est déjà un paramètre (`audioCodec`). Même `-ss`/`adelay`/`volume=eval=frame`/`amix normalize=0` que l'export : **ce qu'on entend est ce qu'on exporte**, un seul chemin de vérité.
2. **`src/window/Editor.cpp`** — après `sceneBuilt()`, si `_scene->_inputs` a un `Sound` ou un `Video` avec piste : `QProcess` (copie de `startExport`) qui écrit `QStandardPaths::TempLocation/video-code-preview-<pid>.wav`, `workingDirectory` = dossier de la scène (les chemins de `Sound("clips/x.wav")` sont relatifs, même raison que la copie `.export.py`). Signal `previewAudioReady()`. Clé de cache = la chaîne de commande : un ⌘S qui ne change que le visuel ne remixe pas. Un run pendant un mix → `kill` + relance ; l'ancien WAV reste jouable entre-temps. Coût mesurable : 100–300 ms pour 30 s de scène (PCM, pas d'encodage) ; `ffprobe` par `Video` ~50 ms.
3. **`src/window/PreviewAudio.{hpp,cpp}`** (nouveau) — `ma_decoder_init_file(wav)` + `ma_device` playback dont le callback lit le décodeur. Exposé au QML : `load(path)`, `play()`, `pause()`, `seek(s)` = `ma_decoder_seek_to_pcm_frame(s*48000)`, `position()` = échantillons lus / 48000 (atomic écrit dans le callback). `#define MINIAUDIO_IMPLEMENTATION` dans ce seul TU.
4. **`qml/VideoCode/Main.qml`** — `onPlayingChanged` → `play()/pause()` ; `onSeek` (~3378, ~3417) → `seek(playhead)` (le scrub stoppe la lecture, ~3391, donc seek seul, pas de son sous la souris cette nuit). **Le `Timer` (~3249) : quand l'audio joue, `next = audio.position()` au lieu de `playhead + 1/execFps`.** C'est le point clé : le Timer QML est une horloge d'images, pas de temps — le rendu est à la demande sur le thread GUI, chaque tick glisse de quelques ms, et après 10 s les lèvres sont décalées. Avec l'audio maître, l'imprécision du Timer devient du jitter (< 1 image), plus une dérive.

Ordre : 1 → tester la commande à la main sur un exemple (`afplay` sur le WAV) → 3 → 2 → 4. Vitesse de lecture : pas cette nuit (le pitch bougerait ; `ma_resampler` plus tard).

## Ce qui peut casser
- L'offset d'entrée oublié quelque part → mix décalé d'une piste. Un test qui compare `buildAudioArgs(…,1)` à l'ancienne chaîne, octet pour octet.
- `amix duration=longest` : le WAV peut dépasser la scène ; la fin de scène met en pause, ne laisse pas jouer.
- Range in/out : seek seul, pas d'`atrim` — le WAV couvre toute la scène.
- Latence device miniaudio ~10 ms, sous la demi-image : ignorer.
- Une scène sans son : pas de WAV, le Timer garde son horloge d'images (branche `else`, ne pas la supprimer).
- Un remix pendant la lecture : `load()` du nouveau WAV en gardant `position()`, sinon la lecture saute à 0 à chaque ⌘S.

## La bonne architecture, et ce qui reste
- **L'horloge maître est le device audio** (compteur d'échantillons), jamais un Timer. L'image poursuit l'horloge : `frame = floor(position * SCENE_FRAMERATE)`. C'est ce que font ffplay et mpv par défaut. Cette décision est prise cette nuit et ne se reprend pas.
- **Pas de mixage « image par image »** : la granularité audio est 1600 échantillons par image, et les rampes revendiquées sont déjà des paliers par image (`eval=frame`). À terme : mixeur en process avec libav (déjà lié : décodage `avformat/avcodec/swresample`), gain par image lu dans `getMetadata(frame).args()["volume"]`, somme vers un ring buffer que le même callback miniaudio consomme. Gains : zéro fichier temporaire, un changement de volume audible en < 1 ms après ⌘S, son sous le scrub (jouer les 1600 échantillons de l'image), vitesse par resampler.
- **Ce qui reste du chemin minimal** : `PreviewAudio` entier (device, horloge, contrat QML `play/pause/seek/position`) — seule la source change, `ma_decoder` sur WAV → mixeur. Et `volumeExpression` : en extraire dès cette nuit `volumeRuns(input, frames)` qui rend le vecteur de paliers, consommé par l'expression ffmpeg aujourd'hui et par le mixeur demain. C'est la seule couture à poser maintenant ; le reste se remplace sans toucher au QML.
