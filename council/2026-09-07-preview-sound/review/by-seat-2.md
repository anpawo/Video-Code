# Relecture croisée — siège 2

## 1. Classement
1. **E** — la plus complète et la plus vérifiée sur le dépôt : `firstInput`, miniaudio par vcpkg, un WAV par révision (jamais réécrit sous le lecteur), `onPlayheadChanged` comme point de seek unique (couvre le caret l.2142, `jumpToMark`, `control()`), et le seul check qui prouve la parité : md5 des PCM du WAV contre la piste du `--generate`.
2. **D** — meilleur raisonnement d'horloge et deux pièges réels que les autres n'ont pas : `Math.max(playhead, position)` contre le démarrage non instantané du device, et une constante d'offset de latence réglable ; mtime dans la clé de cache.
3. **B** — a trouvé les 6 raccourcis (`Main.qml:3557-3572`) qui bougent `playhead` sans couper la lecture, le cache de `hasAudioStream`, le « pas de bake en headless » ; mais Linux muet et un second Timer = deux écrivains de `playhead`.
4. **A** — juste sur le fond (workingDirectory pour les chemins relatifs, garder la position au rechargement) mais `ma_decoder + ma_device` à la main là où `ma_engine` fait la même chose en moitié moins de lignes, et rate le démarrage non instantané et les raccourcis.
5. **C** — l'entrée 0 factice `nullsrc` pour garder les indices est un hack (génère des images pour rien, à `-vn`-er) là où un paramètre coûte 5 lignes ; Linux muet ; le reste est correct mais déjà dit mieux ailleurs.

## 2. Contradictions et arbitrage
| Point | Camps | Arbitrage |
|---|---|---|
| Lecteur | miniaudio (A, D, E) / AVFoundation + stub (B, C) | **miniaudio, port vcpkg** : un seul code, Linux inclus, curseur à l'échantillon. AVFoundation seulement si `vcpkg install miniaudio` échoue (header-only : il n'échouera pas). |
| WAV en RAM / streamé | D : `MA_SOUND_FLAG_DECODE` / E, A : stream | **RAM** : 11 Mo/min, seek instantané, zéro I/O dans le callback. Streamer quand quelqu'un fait une scène de 30 min. |
| Horloge | corps du tick (A, C, D, E) / second Timer 16 ms (B) | **Corps du tick existant** : un seul écrivain de `playhead`, la branche `else` image-par-image reste pour les scènes muettes. |
| Indices d'entrée | paramètre `firstInput` (A, B, D, E) / entrée factice (C) | **Paramètre**, défaut 1, commande du mux identique à l'octet. |
| Clé de cache | commande (A, B, C) / commande + mtime (D) / révision (E) | **Commande + mtime des fichiers** : un clip réexporté sous le même nom doit remixer. |
| API miniaudio | `ma_engine/ma_sound` (D, E) / `ma_decoder/ma_device` (A) | `ma_engine` : moins de code, même header. |
| Vitesse ≠ 1 | `set_pitch` (E) / son coupé (D) / rien (A, B, C) | **Son coupé hors 1×** : une voix de canard devant des testeurs est pire que le silence. |

## 3. Ce que les cinq ont raté
- **Un bouton mute.** Le 09/09 c'est une salle avec des testeurs : chaque Espace va jouer de la musique. Une propriété `muted` + touche M, 5 lignes, absente des cinq réponses.
- **La clé de cache coûte ce que le cache évite** : construire la commande appelle `volumeExpression` (frames × sons `getMetadata`) et `hasAudioStream` (`popen ffprobe` par `Video`) sur le thread GUI à **chaque** ⌘S, même quand le WAV ne change pas. B cache ffprobe ; personne ne dit que la clé elle-même est le vrai coût.
- **Le basculement d'horloge en vol** : play pressé avant la fin du mix → image-par-image, puis le WAV arrive. Il faut `audioPlay(playhead)` à cet instant, pas `play()` depuis 0, et accepter un saut d'une image. E l'effleure, personne ne l'écrit.
- **Ouvrir le device audio tard** : l'init CoreAudio prend 100–300 ms ; à la première lecture, jamais au lancement (un `--check-chrome` n'a pas à toucher la carte son).

## 4. Marche à suivre (6 étapes)
1. `AudioMix.{hpp,cpp}` : déplacement pur des quatre fonctions + `firstInput`/`mapVideo` ; test = commande de mux identique à l'octet ; digest 50 scènes intact.
2. `vcpkg.json` + `miniaudio`, un TU `Speaker.cpp` avec `ma_engine`, 4 `Q_INVOKABLE` (`audioPlay(at)`, `audioPause`, `audioSeek`, `audioPosition` → -1 si muet) + `muted`. Device ouvert au premier play.
3. `Editor::sceneBuilt()` → `QProcess` ffmpeg vers `<tmp>/preview-<pid>-<rev>.wav`, `workingDirectory` = dossier de la scène, clé = commande + mtime, `hasAudioStream` caché par chemin, rien en headless.
4. `Main.qml` : tick = `p < 0 ? playhead + 1/execFps : Math.max(playhead, p)` ; `onPlayingChanged` → play/pause ; `onPlayheadChanged` quand `!playing` → seek (couvre caret, marques, raccourcis, `control()`).
5. À `finished` pendant une lecture : `load` + `audioPlay(playhead)`.
6. Preuve : md5 des PCM du WAV contre la piste du `--generate` sur une scène `Sound + duck + Video`, puis une écoute humaine — seul juge de la latence, offset réglable si l'image est en avance.
