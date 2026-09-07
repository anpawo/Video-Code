# Siège 1 — le son de l'aperçu

## Recommandation ferme

**Pré-mixer un WAV par exécution avec exactement le graphe ffmpeg du rendu, le jouer avec miniaudio, et faire de l'audio l'horloge maîtresse dès qu'un son existe.** Pas de qtmultimedia : QAudioSink ne décode ni ne mixe rien, et il coûte un rebuild de Qt pour ce qu'un header de 1 fichier fait mieux.

## 1. Le chemin d'une nuit (≈ 250 lignes, 4 h, macOS + Linux d'un coup)

Ce qui rend ça court : la scène tourne **déjà en process** dans l'éditeur (`Editor::sceneBuilt()` → `Core::rebuildFromContext()`, `_scene->_inputs` est public, `getMetadata(frame)` répond). Le mix du rendu est donc calculable dans l'éditeur sans rien inventer.

Ordre des étapes :

1. **`src/compiler/Compiler.cpp` → `src/compiler/AudioMix.cpp` + `include/compiler/AudioMix.hpp`.** Sortir de l'anonyme `hasAudioStream`, `videoAudioChain`, `volumeExpression`, `buildAudioArgs`, et couper `buildAudioArgs` en deux : le graphe (`inputs`, `filterComplex`, `outLabel`, `count`, avec un paramètre `firstInput` car le rendu a le pipe rawvideo en entrée 0 et l'aperçu non) et le formatage `-map 0:v -map [..] -c:a` qui reste dans `generateVideo`. Zéro changement de comportement : **le digest du bake 50 scènes doit sortir identique**, c'est la preuve.
2. **`vcpkg.json` : `"miniaudio"`** (header-only, port vcpkg, CoreAudio + PulseAudio/ALSA, s'installe en secondes, pas de rebuild Qt). `CMakeLists.txt` : `find_path(MINIAUDIO_INCLUDE_DIRS miniaudio.h)` + un TU `src/window/Speaker.cpp` avec `#define MINIAUDIO_IMPLEMENTATION`. API utilisée : `ma_engine_init`, `ma_sound_init_from_file(…, MA_SOUND_FLAG_STREAM)`, `ma_sound_seek_to_pcm_frame`, `ma_sound_start/stop`, `ma_sound_get_cursor_in_seconds`, `ma_sound_set_pitch` pour la vitesse.
3. **`src/window/Editor.cpp`** : à la fin de `sceneBuilt()`, `mixPreviewAudio()` : tuer le `QProcess` précédent, lancer `ffmpeg -y <inputs> -filter_complex "<graphe>" -map "[out]" -ar 48000 -ac 2 -c:a pcm_s16le <tmp>/video-code-preview-<pid>-<rev>.wav` (QProcess, **jamais popen** : le mix d'une scène de 3 min prend ~1 s, pas sur le thread GUI). À `finished` : `_speaker.load(wav)`, supprimer le WAV de la révision d'avant, `Q_EMIT hasAudioChanged`. Exposer `Q_PROPERTY(bool hasAudio)`, `Q_INVOKABLE audioPlay(double at)`, `audioPause()`, `audioSeek(double)`, `double audioCursor()`, `audioRate(double)`.
4. **`qml/VideoCode/Main.qml`** : le `Timer` (~3249) devient `next = shell.hasAudio ? shell.audioCursor() : playhead + 1/execFps` — l'audio est l'horloge, la frame s'aligne dessus. `onPlayingChanged` : `playing ? shell.audioPlay(playhead) : shell.audioPause()`. `onPlayheadChanged` quand `!playing` : `shell.audioSeek(playhead)` (le scrub met déjà `playing = false` avant de bouger la tête, l. 3416 ; `PreviewPanel.onSeek` l. 3378 ne le fait pas → seek si `|playhead − cursor| > 2/fps`). Fin de plage `markOut` : la logique actuelle suffit.
5. **Un seul check** : `--check-chrome` sur une scène `Sound + music.duck(under=voice) + Video` ; asserter que le WAV existe et que ses PCM décodés sont identiques (md5 via `ffmpeg -f s16le`) à la piste de `--generate` de la même scène. Même graphe ⇒ mêmes échantillons ; s'ils divergent, l'aperçu ment.

Ce qui vient gratuitement : `start` (`adelay`), `trim` (`-ss/-to`), `volume`, les rampes de duck (`volume=…:eval=frame`), l'`atempo` des `Video`, `amix normalize=0` — c'est le code du rendu.

Pièges, dans l'ordre où ils mordront :
- **Dérive** : le Timer actuel est une horloge de frames (33 ms arrondis ≠ 33,33) : 1 %/min de décalage à lui seul, plus chaque rendu lent. D'où l'audio maître : la frame saute, le son ne traîne jamais (c'est ce que fait tout lecteur).
- **Boucle de seek** : ne jamais seeker sur le tick d'horloge (glitch à chaque frame) ; seek uniquement sur une tête posée par l'humain.
- **WAV pas prêt** : play pressé avant `finished` → lire muet sur l'horloge de frames, basculer sur l'audio à `hasAudioChanged`. Ne pas bloquer.
- **`hasAudioStream` popen ffprobe** synchrone par `Video` (~50 ms chacune) : tolérable pour le 09/09, à cacher par chemin ensuite.
- **`ma_sound_set_pitch`** change hauteur ET vitesse (effet bande) : acceptable en aperçu, `ponytail:` à noter, resampler si quelqu'un s'en plaint.
- **Latence** CoreAudio ~10 ms, sous une frame : ignorer. Taille : 10 min = 115 MB de WAV, streamé, pas chargé.
- `ffmpeg` sur le PATH : l'export en dépend déjà, même hypothèse.

## 2. L'architecture cible, et ce qui survit

- **L'audio reste l'horloge maîtresse quand il y a du son, la frame sinon.** C'est le seul point non négociable et il est acquis dès cette nuit.
- **Le WAV pré-mixé tient longtemps** : le graphe audio est statique entre deux exécutions, et une édition ré-exécute de toute façon. Le vrai coût est la seconde de mix après chaque édit, pas la conception.
- Quand cette seconde gêne : remplacer le `QProcess` par **libavfilter en process** — `avfilter_graph_parse2` avale **la même chaîne `filterComplex`**, libav* est déjà lié — poussant dans un `ma_pcm_rb` lu par le callback miniaudio. Plus de fichier, plus de process, seek = re-graph à `t`. Mix temps réel « image par image » côté C++ : non — c'est réinventer `volume=eval=frame` en moins bien.
- Survit du chemin minimal : `AudioMix.hpp` (le graphe partagé rendu/aperçu, qui garantit qu'on entend ce qu'on exporte), l'API `Speaker` (play/pause/seek/cursor), la règle d'horloge en QML. Meurt : le WAV et le `QProcess`, ~40 lignes.
