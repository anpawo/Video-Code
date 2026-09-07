# Siège 4 — le son de l'aperçu

**Ferme : pré-mixer un WAV avec EXACTEMENT le code ffmpeg du rendu, le jouer via AVFoundation derrière une façade
à 4 fonctions (stub Linux), et faire de l'audio l'horloge maître pendant la lecture.** Pas de qtmultimedia, pas de
dépendance, pas de rebuild vcpkg. ~250 lignes, une nuit.

Trois faits du dépôt qui tranchent :
- L'éditeur **construit déjà la scène en process** : `Editor::sceneBuilt()` remplit un `Core`, donc `_scene->_inputs`
  est le vecteur même que `generateVideo()` passe à `buildAudioArgs`. Aucun IPC, aucun re-parse : le mix de l'aperçu
  peut littéralement être le mix du rendu.
- Le motif **« natif macOS + stub »** existe déjà (`src/window/MacApplication.mm` / `MacApplicationStub.cpp`, ObjC++
  déjà dans le build, `CMakeLists.txt:212`). AVAudioPlayer coûte un `-framework AVFoundation` ; qtmultimedia coûte un
  rebuild vcpkg **et** les imports de plugins statiques (cf. le pavé `Qt6::qtquick2plugin`, l. 302) pour un lecteur de
  fichier qu'AVFoundation donne gratis, et traîne gstreamer sur Linux. Non.
- **Aucun seek pendant la lecture n'existe** : `onScrubbed`, `onSeek`, `jumpToMark` font tous `playing = false`
  d'abord. L'API se réduit à `play(from)` / `stop()` / `at()`, toute la resynchro en vol disparaît. Exception : les
  raccourcis `Main.qml:3557-3572` (Home/End/±1 image) bougent `playhead` sans couper la lecture → les router par un
  `app.seekTo(t)` unique, 6 sites.

## Chemin minimal, dans l'ordre
1. `include/compiler/AudioMix.hpp` — sortir `hasAudioStream`, `videoAudioChain`, `volumeExpression`, `buildAudioArgs`
   du namespace anonyme de `Compiler.cpp` (header, `inline`). Ajouter `bool withVideo = true` : `tracks + 1` devient
   `tracks + (withVideo ? 1 : 0)` et `-map 0:v ` est omis. 5 lignes touchées, zéro changement pour le rendu. Extraire
   au passage la rampe en fonction pure `gainExpression(const std::vector<double>& perFrame, double fallback)`.
2. `test/cpp/unit_test.cpp` — le check qui manque : `gainExpression` sur une rampe de duck (fusion des runs égaux,
   dernier terme sans borne haute, repli moyenne au-delà de 32 000 caractères). La cible compile contre `include/`
   seul, elle reste à 1,5 s.
3. `include/window/PreviewAudio.hpp` + `src/window/MacAudio.mm` + `MacAudioStub.cpp` :
   `bool audioOpen(const QString& wav); void audioPlay(double at); void audioStop(); double audioAt();` — le `.mm` est
   un `AVAudioPlayer` statique, `currentTime = at` puis `[p play]`, `audioAt()` rend `currentTime` ; le stub rend `false`/`0`.
4. `Editor.cpp` — `bakeAudio()` construit
   `ffmpeg -y {audio.inputs} -filter_complex "…" -map "[aout]" -c:a pcm_s16le -ar 48000 -ac 2 <cache>/preview.wav`
   depuis `buildAudioArgs(_scene->_inputs, "pcm_s16le", std::nullopt, frames, /*withVideo=*/false)`, lancé en
   `QProcess` (motif `startExport`, `Editor.cpp:1206`), **la chaîne de commande servant de clé de cache** : une édition
   qui ne touche pas au son donne la même commande, donc zéro re-bake. À chaque `executeScene` réussi, jamais si
   `_headless`. Fenêtre `nullopt` : on mixe toute la timeline en absolu et on cherche dedans — le raisonnement déjà
   écrit sur `window`.
5. `CMakeLists.txt` : les deux sources à côté de `MacApplication`, `-framework AVFoundation`.
6. `Main.qml` : `togglePlay()` → `Shell.audioPlay(playhead)` / `Shell.audioStop()` ; `clock.running: app.playing &&
   !app.soundReady` ; un second `Timer` à 16 ms, `running: app.playing && app.soundReady`, fait `app.playhead = Shell.audioAt`.

## Ce qui casse
- **L'aperçu se met à sauter des images.** L'horloge actuelle est une horloge d'images assumée (commentaire l. 3243)
  et dérive du temps réel par construction ; dès qu'il y a du son, c'est le son qui ne peut pas sauter, donc l'image
  chasse. Changement de comportement voulu, à dire tout haut. Sans son, rien ne bouge.
- Digest 50 scènes et goldens ne bronchent pas à l'étape 1 : exporter une scène avec son avant/après, comparer les hashes.
- `hasAudioStream` fait un `popen ffprobe` **synchrone** par `Video` pendant la construction de la commande, donc sur
  le thread UI → cache `static std::map<path, bool>`.
- Le repli « moyenne » au-delà de 32 000 caractères et le plancher `atempo=0.5` (source > 60 fps) frappent l'aperçu
  comme le rendu : correct, l'aperçu doit mentir de la même façon.
- Recréer l'`AVAudioPlayer` après chaque bake (le WAV est réécrit sous lui). Runs scriptés (`control()` play/pause,
  `--check-widget`) : aucun bake, aucun device.

## À terme
Le bake reste la vérité — réimplémenter le mix côté éditeur est le seul endroit où l'aperçu commencerait à mentir.
S'ajoutent, dans cet ordre : (a) bake **par piste**, caché sur la chaîne de filtre de cette piste, joué dans un
`AVAudioEngine` à un `AVAudioPlayerNode` par `Sound`/`Video` — c'est ce qui tue le re-mix complet sur une scène de dix
minutes ; (b) le WAV lu en mémoire, ce qui débloque le scrub audio (un grain court autour de la tête pendant le drag) ;
(c) Linux via miniaudio (un header) derrière les mêmes 4 fonctions ; (d) `enableRate`/`rate` pour la vitesse. L'audio
reste maître : une image sautée ne s'entend pas, un échantillon sauté s'entend.
