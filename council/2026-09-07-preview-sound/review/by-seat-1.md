# Relecture croisée — siège 1

## 1. Classement
1. **B** — la seule à avoir lu le QML jusqu'aux raccourcis Home/End/±1 (l. 3557-3572) qui bougent la tête sans couper la lecture, à penser aux runs scriptés (`control()`, `--check-chrome` : pas de device), et à vouloir un test unitaire de la rampe ; le second Timer et le `.mm` mac-only sont ses deux faiblesses.
2. **C** — le raisonnement le plus net sur l'horloge (« l'audio est maître dès qu'il y a du son, l'image au scrub ») et l'`AudioArgs` découpé en `filter`/`label`, ce qui lui évite le piège `[aout]` ; l'input 0 factice en `lavfi` est une verrue.
3. **D** — la vérif « même `filter_complex` aux indices près », le `Math.max` contre le curseur qui recule au démarrage, et la seule à laisser un bouton d'offset A/V ; mais `-map "[aout]"` en dur et miniaudio vendoré plutôt que le port vcpkg.
4. **E** — complet et bien ordonné, le WAV nommé par révision (évite d'écraser le fichier sous le lecteur), mais rien que les autres n'aient dit et `-map "[out]"` est faux aussi.
5. **A** — bonne idée de la clé de cache = commande, mais `-map "[aout]"` en dur, un `workingDirectory` = dossier de scène que l'export **ne** fait pas (divergence aperçu/export), et un `ma_device` + décodeur à la main là où `ma_engine` fait le travail.

## 2. Contradictions, et l'arbitrage
| Sujet | Positions | Arbitrage |
|---|---|---|
| miniaudio / AVFoundation | A, D, E : miniaudio (port vcpkg, Linux gratuit) ; B, C : AVAudioPlayer + stub, zéro dépendance | **miniaudio** : même code sur les deux OS, curseur à l'échantillon ; AVAudioPlayer laisse Linux muet et `currentTime` est approximatif. Le port est dans le cache vcpkg. |
| RAM (D, `DECODE`) / streaming (E, `STREAM`) / décodeur manuel (A) | | **`DECODE` en RAM** : 3 min ≈ 33 Mo, seek instantané, et surtout le fichier est fermé après chargement — ce qui permet de le réécrire. Streaming le jour où quelqu'un a une scène de 30 min. |
| Remplacer le tick (A, C, D, E) / second Timer 16 ms (B) | | **Un seul Timer**, `onTriggered` lit le curseur : deux horloges qui écrivent `playhead`, c'est le bug de demain. |
| Cache du WAV | A, B, C, D : clé = commande ; E : remix à chaque run | **Clé = commande** (+ mtime des fichiers, D) : un ⌘R visuel ne doit pas relancer ffmpeg. |
| Fenêtre `markIn/markOut` | tous : WAV absolu, jamais `atrim` | Unanimité, juste. |
| Vitesse ≠ 1 | E : pitch tape ; D : couper le son ; A, B : pas cette nuit | **Pas cette nuit.** |

## 3. Ce que les cinq ont raté ou sous-estimé
- **`[aout]` n'existe que s'il y a ≥ 2 pistes** (`Compiler.cpp:213`, `outLabel = "a0"` sinon) : A, B, D, E figent le label → la scène de démo à une musique **échoue silencieusement**. Le label doit sortir de `buildAudioArgs`.
- **L'échec est muet.** Toutes disent « jouer muet si le WAV n'est pas prêt » ; aucune ne dit *ce qu'on fait quand ffmpeg échoue*. Une app lancée depuis le Dock a un `PATH` sans `/opt/homebrew/bin` : `ffmpeg` introuvable, aucun WAV, et le bug d'origine (« le son ne marche pas ») revient tel quel devant les testeurs. Résoudre `ffmpeg` avec `QStandardPaths::findExecutable` + `/opt/homebrew/bin`, et `source.say()` la raison à chaque échec du `QProcess`.
- **Le budget de synchro n'est jamais additionné** : curseur miniaudio ≠ sortie HP (~10-20 ms), rendu à la demande sur le thread GUI après lecture du curseur (10-30 ms), et `PreviewPanel.qml:78` fait `Math.round(playhead × fps)` là où l'export choisit `floor` — une demi-image d'avance systématique. Total : entre −16 et +60 ms, à cheval sur le seuil de perception (~45 ms). Passer à `Math.floor`, et garder le bouton d'offset de D.
- **Réécrire `preview.wav` sous le lecteur** (A, B, C, D) : `ffmpeg -y` tronque un fichier que miniaudio tient ouvert. Nom par révision, ou `DECODE` puis suppression.

## 4. Marche à suivre pour cette nuit
1. `include/compiler/AudioMix.hpp` + `.cpp` : déplacement pur des quatre fonctions, paramètre `firstInput`, `AudioArgs{inputs, filter, label, count}` ; `generateVideo` recompose `-map 0:v -map [label] -c:a`. Bake 50 scènes identique, puis un test unitaire de la rampe (B).
2. `vcpkg.json` : `miniaudio` ; `src/window/Speaker.cpp` (`MINIAUDIO_IMPLEMENTATION`, `ma_engine`, `DECODE`) exposé par 4 `Q_INVOKABLE` + `Q_PROPERTY(bool hasAudio)` sur `Editor`, aucun device en `--headless`.
3. `Editor::bakeAudio()` après `sceneBuilt()` : commande depuis `AudioMix`, clé de cache = commande + mtime, `QProcess` avec `ffmpeg` résolu explicitement, WAV `<tmp>/video-code-preview-<pid>-<rev>.wav`, échec → `Q_EMIT said("no sound: …")`.
4. `Main.qml` : un `app.seekTo(t)` unique pour les 6 sites qui posent la tête (scrub, seek, marks, Home/End/±1) → `audioSeek` ; `togglePlay` → `audioPlay(playhead)` / `audioPause()` ; le Timer lit `Math.max(playhead, audioCursor())` quand `hasAudio`, l'incrément d'image sinon ; `PreviewPanel` passe à `Math.floor`.
5. Vérif : PCM du WAV == PCM de la piste `--generate` sur une scène `Sound + duck + Video` **et** sur une scène à une seule piste ; `--check-chrome` avec `control(play)`.
6. Le dire tout haut à Marius : l'aperçu saute désormais des images sous une pane lente, il n'y a pas de son au scrub ni de vitesse ≠ 1, et Linux joue via PulseAudio sans test réel.
