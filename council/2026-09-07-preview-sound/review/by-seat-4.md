# Relecture croisée — siège 4

Les cinq disent la même chose sur le fond : WAV pré-mixé par le graphe ffmpeg du rendu, code partagé sorti de l'anonyme, audio horloge maître, pas de qtmultimedia. Le désaccord est entièrement dans les détails, et c'est là que la nuit se gagne ou se perd.

## 1. Classement
1. **D** — la seule à avoir vu les pièges qui mordent vraiment : `Math.max` sur la course au démarrage (le curseur rend ~0 les premiers ticks, la tête recule sinon), l'offset A/V laissé réglable par défaut 0, décodage en RAM, une seule horloge.
2. **E** — la seule avec une vérification qui prouve quelque chose sans fenêtre (md5 des PCM de l'aperçu contre la piste du `--generate`), et la meilleure coupe : graphe d'un côté, formatage `-map 0:v` de l'autre.
3. **A** — le meilleur diagnostic du *pourquoi* le Timer doit mourir, et la seule à traiter le remix pendant la lecture (garder `position()` au rechargement). Perd une place sur un `workingDirectory` qui est un contresens (voir §2).
4. **B** — trouve le fait qui supprime le plus de travail (aucun seek pendant la lecture n'existe : `onScrubbed`/`onSeek`/`jumpToMark` coupent tous la lecture d'abord) et le seul test unitaire sur les rampes ; mais son second Timer est une horloge de trop et AVFoundation abandonne Linux sans rien gagner.
5. **C** — juste sur toute la structure, mais son entrée 0 factice `-f lavfi nullsrc` fait décoder une vidéo pour rien alors que `firstInput = 0` règle la question, et c'est la plus vague sur l'API et sur le chemin d'échec.

## 2. Contradictions et arbitrage
- **miniaudio (A, D, E) contre AVFoundation (B, C)** → **miniaudio**. Un seul chemin pour mac et Linux, et surtout un vrai curseur d'échantillons lu dans le callback ; `AVAudioPlayer.currentTime` est une estimation par quantum de rendu, ce qui est précisément ce qu'on veut arrêter d'accepter en devenant horloge maître. Vérifier le port vcpkg au premier `install` ; s'il ne répond pas, le header vendoré (D) et on continue, ça ne vaut pas dix minutes de débat.
- **RAM (D) contre streaming (E, et B/C par nature)** → **RAM** (`MA_SOUND_FLAG_DECODE`, ~33 Mo pour 3 min). Ce n'est pas la taille qui tranche, c'est que ffmpeg réécrit le WAV pendant que le lecteur y lit.
- **Remplacer le tick (A, C, D, E) contre second Timer (B)** → **remplacer**. Deux objets qui bougent `playhead` se disputeront l'image de fin de plage ; une ligne, une branche, un `else` qui garde l'horloge d'images pour les scènes muettes.
- **`firstInput` (A, D, E) contre `withVideo` (B) contre `nullsrc` (C)** → la coupe d'**E** : `buildAudioGraph()` rend `{inputs, filter, label}`, `generateVideo()` garde `-map 0:v -c:a`. La question de l'entrée 0 disparaît au lieu d'être paramétrée.
- **`workingDirectory` = dossier de la scène (A)** → **non**. `_besideScene` ne touche que `sys.path`, jamais le cwd : les chemins relatifs des médias se résolvent déjà contre le cwd du process au rendu. Changer le cwd de l'aperçu le ferait diverger du rendu — exactement ce que les cinq ont juré d'éviter.

## 3. Ce que les cinq ont raté
- **La panne reste silencieuse.** Le bug rapporté est « le son ne marche pas ». ffmpeg absent, fichier de son déplacé, `atempo` sous 0,5, mix pas fini au premier Espace : les cinq répondent « jouer muet, ne jamais bloquer ». Marius rappuie sur Espace et n'entend rien — le bug d'aujourd'hui, avec 250 lignes de plus. L'échec doit parler (`source.say`, StatusStrip) et **le premier Espace doit attendre le mix en le disant** ; 300 ms annoncées valent mieux qu'un silence inexpliqué.
- **Le cache ne protège pas ce qui coûte.** Les cinq hachent la commande pour éviter le re-spawn — mais cette commande est produite par `hasAudioStream` (`popen ffprobe` synchrone, ~50 ms par `Video`, sur le thread GUI) et par `volumeExpression` (images × entrées appels à `getMetadata`), à chaque exécution, donc à chaque pause de frappe. La clé est calculée par le travail qu'elle prétend éviter.
- **Personne n'a les deux moitiés du même piège** : D décode en RAM mais garde un nom de fichier fixe, E prend un nom unique par révision mais streame. Il faut les deux, plus la suppression de l'ancien WAV.

## 4. Marche à suivre, cette nuit
1. `include/compiler/AudioMix.hpp` + `src/compiler/AudioMix.cpp` : déplacement pur, `buildAudioGraph(inputs, frames, firstInput)` → `{inputs, filter, label, count}` ; `generateVideo` garde son formatage. Mémoïser `hasAudioStream` par chemin. **Preuve avant d'aller plus loin : digest 50 scènes inchangé et un export avec son identique à l'octet.**
2. `src/window/Speaker.{hpp,cpp}` (TU unique avec `MINIAUDIO_IMPLEMENTATION`) : `load/play(at)/pause/seek/cursor`, `ma_sound_init_from_file(MA_SOUND_FLAG_DECODE)`. L'API ressemble à un lecteur, jamais à un fichier.
3. `Editor::bakeAudio()` après `sceneBuilt()` : QProcess (motif `startExport`), `<tmp>/video-code-preview-<pid>-<rev>.wav`, cwd inchangé, `window = nullopt`, hash de commande, ancien WAV supprimé à `finished`, dernière ligne de stderr remontée à la StatusStrip. Rien si `_headless`.
4. `Main.qml`, un seul Timer : `const p = Shell.audioCursor(); playhead = p < 0 ? playhead + 1/execFps : Math.max(playhead, p)`, arrêt sur `until` inchangé ; `togglePlay` → `audioPlay(playhead)` / `audioPause()`. Premier Espace pendant un mix : attendre, et le dire.
5. Vérifier sans fenêtre : md5 des PCM `s16le` du WAV d'aperçu contre la piste du `--generate` de la même scène (`Sound` + `duck` + `Video`) ; plus le test unitaire sur les paliers de `volumeExpression` dans `test/cpp/unit_test.cpp`.
6. Dire tout haut ce qui n'est pas fait : pas de son au scrub, pas de vitesse ≠ 1, Linux muet si miniaudio manque, offset A/V réglable à 0 — et que l'image saute désormais des frames plutôt que de traîner le son.
