# Relecture croisée — siège 5

## 1. Classement

1. **E** — la seule qui ait lu les chemins de seek juste (`PreviewPanel.onSeek`, l. 3378, ne coupe **pas** la lecture : vérifié), qui nomme la boucle seek↔tick, et qui propose une vraie preuve (md5 des PCM de l'aperçu contre la piste du `--generate`).
2. **A** — meilleure liste de « ce qui casse », seule à voir que `Sound("clips/x.wav")` est relatif donc que le `QProcess` a besoin d'un `workingDirectory` ; `firstInput` par défaut à 1 garde la commande de rendu identique à l'octet. Descend au niveau `ma_decoder`+`ma_device` là où `ma_engine` suffisait.
3. **D** — les deux meilleurs détails isolés du conseil : le `Math.max` contre le playhead qui recule au démarrage du device, et la constante d'offset de latence. Mais elle vendore `miniaudio.h` à la main alors que le port vcpkg existe : plus de travail pour un fichier de plus dans le dépôt.
4. **B** — excellente section long terme (bake par piste) et le seul test unitaire proposé, mais sa prémisse porteuse est fausse — « aucun seek pendant la lecture n'existe » —, donc son API `play/stop/at` sans seek est conçue sur du vide.
5. **C** — juste sur le fond (label dynamique, audio maître) mais n'a jamais envisagé miniaudio : elle livre macOS seul et qualifie le silence sous Linux XCB — une cible du projet — de choix assumé, alors que c'est un angle mort. Aucune vérification proposée.

## 2. Contradictions, et mon arbitrage

- **miniaudio vs AVFoundation → miniaudio.** Le port existe (`$VCPKG_ROOT/ports/miniaudio`, 0.11.25, header-only, `file(INSTALL miniaudio.h)`) : l'installer est un téléchargement, pas un rebuild de Qt. Un seul chemin pour macOS **et** Linux. Je tranche contre ma propre réponse.
- **Vendoré (D) vs port → le port.** Rien à mettre à jour à la main.
- **RAM (`MA_SOUND_FLAG_DECODE`) vs streaming → RAM.** 3 min stéréo 48 kHz = 34 Mo, et le seek devient un déplacement de pointeur — c'est exactement ce dont Home/End/±1 image ont besoin.
- **Remplacer le tick vs second Timer (B) → remplacer le tick.** Deux horloges à tenir d'accord, et il faudrait dupliquer l'arrêt sur `until`/`markOut` que le tick actuel porte déjà.
- **Paramètre `firstInput` vs entrée factice `-f lavfi -i nullsrc` (C) → le paramètre.** L'entrée factice décode un flux vidéo pour rien et laisse un `-map 0:v` à retirer ensuite.

## 3. Ce que les cinq ont raté

- **Aucune n'a vérifié quand `executeScene` tourne.** ⌘R, ouverture de fichier, édition d'agent — **pas la frappe** (`Main.qml:1466` : *« the timeline only moves on ⌘R »*). Les cinq ont donc spécifié un cache par hash de commande contre un coût qui survient quelques fois par minute, en arrière-plan. Pire : la clé se calcule *après* le `popen ffprobe` par `Video` et le parcours frames × inputs de `volumeExpression` — **la clé coûte ce qu'elle prétend éviter.** À couper ce soir.
- **La latence de sortie est sous-estimée par les cinq.** Quatre écrivent « ~10 ms, ignorer » ; la cinquième laisse un bouton à 0 sans dire pourquoi. Sur AirPods, CoreAudio sort à 150–250 ms : 5 à 8 images d'écart, visibles, le 09/09, si Marius démontre au casque.
- **Quatre sur cinq codent `-map "[aout]"` en dur.** `outLabel` vaut `"a0"` quand il n'y a qu'une piste : une scène à un seul `Sound` — la démo la plus probable et le premier test — fait échouer ffmpeg. La cinquième sépare le label sans nommer le piège.

## 4. La marche à suivre, cette nuit

1. `include/compiler/AudioMix.hpp` + `.cpp` : déplacer `hasAudioStream`, `videoAudioChain`, `volumeExpression`, `buildAudioArgs` hors de l'anonyme, + `firstInput` (défaut 1) et `mapVideo` (défaut vrai). **Rendre `outLabel` ; ne jamais l'écrire en dur.** Preuve : le digest bake 50 scènes inchangé.
2. `vcpkg.json` : `"miniaudio"`. `CMakeLists.txt` : `find_path`, et un seul TU `src/window/Speaker.cpp` avec `#define MINIAUDIO_IMPLEMENTATION`.
3. `Speaker` = `ma_engine_init` + `ma_sound_init_from_file(..., MA_SOUND_FLAG_DECODE, ...)`, quatre `Q_INVOKABLE` sur `Editor` : `audioPlay(at)`, `audioPause()`, `audioSeek(t)`, `audioPosition()` (`-1` si muet). Plus `audioOffset` en secondes, défaut 0, **réglable** : c'est le bouton de calibration pour le Bluetooth.
4. `Editor.cpp`, à la fin de `sceneBuilt()` : `QProcess` (motif `startExport`, l. 1206) vers `<tmp>/video-code-preview-<pid>-<rev>.wav`, `workingDirectory` = dossier de la scène, `window = nullopt`. Nom par révision : ffmpeg ne doit jamais réécrire sous le lecteur. **Pas de cache** — `ponytail:` re-mix à chaque ⌘R, hasher la commande quand l'attente se sent.
5. `Main.qml` : le tick (l. 3249) lit `Math.max(playhead, Shell.audioPosition() + offset)` quand elle est ≥ 0, sinon l'incrément image. `togglePlay()` → `audioPlay/audioPause`. Router **les six** sites qui bougent `playhead` sans couper la lecture (l. 3378, Home, End, ±1 image, marqueurs) par un `seekTo(t)` unique. Ne jamais seeker depuis le tick.
6. Vérifier sans fenêtre : `--check-chrome` sur une scène `Sound + duck + Video`, puis comparer le md5 des PCM du WAV d'aperçu à ceux extraits du `--generate` de la même scène. Identiques ou l'aperçu ment.
