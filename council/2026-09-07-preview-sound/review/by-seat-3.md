# Relecture croisée — siège 3

Consensus des cinq, acquis : WAV pré-mixé par **le code ffmpeg du rendu**, `buildAudioArgs` sorti de l'anonyme, `window = nullopt`, cache sur la commande, QProcess pas popen, audio horloge maître, pas de qtmultimedia, pas de son au scrub. Le classement porte sur ce que chacune **ajoute**.

## 1. Classement
| # | | Pourquoi |
|---|---|---|
| 1 | **E** | Seule à proposer une preuve : md5 des PCM de l'aperçu contre la piste de `--generate`. WAV nommé par révision (règle le fichier réécrit sous le lecteur). `avfilter_graph_parse2` sur *la même* chaîne comme suite. |
| 2 | **A** | Seule à poser la couture qui survit (`volumeRuns`) et à traiter le remix *pendant* la lecture sans retomber à 0. Chiffre le coût du bake. |
| 3 | **B** | Deux faits ratés par les autres : `MacApplication.mm`/`MacApplicationStub.cpp` existent déjà (vérifié), et aucun seek n'existe en lecture **sauf** `Main.qml:3555-3572`, quatre raccourcis qui bougent `playhead` sans couper. Perd sur le second Timer. |
| 4 | **D** | Juste sur l'horloge, mais son `Math.max` est une défense qui casserait un seek en vol, et elle vendore un header sans avoir vérifié le port. |
| 5 | **C** | Bien raisonnée, mais l'entrée `nullsrc` factice est la mauvaise idée du lot, et « Linux muet » est une demi-réponse sur une cible affichée. |

## 2. Contradictions, et l'arbitrage
- **miniaudio vs AVFoundation** : B/C ont raison sur le précédent `.mm` (je l'avais raté), mais Linux est une cible et le natif se paie deux fois → **miniaudio**, port vcpkg si `vcpkg search miniaudio` répond (30 s ; A et E l'affirment sans preuve au dossier), header vendoré sinon.
- **RAM vs streaming** : faux débat une fois le WAV nommé par révision (E) — rien n'est plus réécrit sous le lecteur. `MA_SOUND_FLAG_DECODE` sous ~5 min, `STREAM` au-delà.
- **Tick remplacé vs second Timer** : **un seul Timer**, branche dedans. Le second (B) duplique la sortie sur `until` et son `spent = until - 1/execFps + 1e-6`, qui est justement le code subtil.
- **`Math.max(playhead, cursor)` (D)** : à jeter — affectation nue, plus une branche « pas prêt → horloge d'images ».
- **`nullsrc` (C) vs `firstInput`** : paramètre. Un décodeur en plus pour masquer un décalage d'indice, non.
- **Latence** : A/E disent « ignorer », D veut un bouton → **bouton, défaut 0**, c'est du matériel.

## 3. Ce que les cinq ont raté
- **La clé de cache se mord la queue.** Toutes disent « clé = la commande » — or *fabriquer* la commande **est** le coût : un `popen ffprobe` synchrone par `Video` (B/E le voient trop tard) + `frames × inputs` appels à `getMetadata`, sur le thread GUI, à chaque exécution, y compris quand le résultat sera identique. La clé doit être bon marché et venir **avant** : chemins, `start`/`trim`/`volume`, mtimes. Et mémoïser `hasAudioStream` par chemin.
- **Le bake qui échoue.** Aucune ne branche l'échec : un `Sound` vers un fichier illisible et l'éditeur croit avoir du son, ou râle à chaque frappe. Échec ⇒ `hasAudio = false`, dit **une fois**.
- **Aucun réglage de sortie.** Ni mute ni volume d'aperçu, alors que `normalize=0` laisse volontairement clipper. `ma_engine_set_volume` + un bouton : trois lignes, et il travaille la nuit.

## 4. La marche à suivre, 6 étapes
1. `AudioMix.{hpp,cpp}` : déplacement pur + `firstInput` et `mapVideo`. Preuve : digest bake 50 scènes inchangé, et une scène sonore exportée identique octet pour octet avant/après.
2. Clé de cache bon marché + mémo `hasAudioStream` par chemin, **avant** toute construction de commande.
3. `Speaker` miniaudio : `load/play/pause/seek/cursor`, `MINIAUDIO_IMPLEMENTATION` dans un seul TU.
4. Bake `QProcess` vers `preview-<pid>-<rev>.wav` ; brancher `finished` succès **et** échec ; effacer la révision d'avant.
5. QML : un Timer, `playhead = hasAudio ? cursor() : playhead + 1/execFps` ; router `Main.qml:3555-3572` par un `seekTo()` unique ; arrêt sur `until` inchangé.
6. Check : md5 des PCM de l'aperçu vs `--generate` sur `Sound + duck + Video`, puis `--check-chrome`, puis il écoute.
