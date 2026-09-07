# Siège 5 — Pré-mix WAV + AVAudioPlayer, et l'audio devient l'horloge maître

**Tranché : pas de qtmultimedia.** Un rebuild vcpkg statique la veille d'une démo pour
obtenir `QAudioSink` — un ring buffer que vous alimentez vous-même — alors que macOS
livre déjà `AVAudioPlayer` (play/pause/`currentTime` en lecture ET en écriture/`rate`),
c'est payer cher un service qu'on a gratuitement. Le projet compile déjà de l'Obj-C++
(`src/window/MacApplication.mm`) avec un stub Linux à côté : c'est exactement la forme
qu'il faut. `-framework AVFoundation` = une ligne de CMake, zéro rebuild vcpkg.

## Le chemin minimal (une nuit, ~250 lignes)

1. **Sortir le graphe audio de l'anonymat.** `buildAudioArgs`, `volumeExpression`,
   `videoAudioChain` sont dans le `namespace {}` de `src/compiler/Compiler.cpp` →
   déplacement pur vers `src/compiler/AudioMix.cpp` + `include/compiler/AudioMix.hpp`.
   Exposer `filter` et `label` séparément dans `AudioArgs` (aujourd'hui collés à
   `-map 0:v` dans `output`) pour que l'éditeur compose sans vidéo. **Un déplacement,
   pas une réécriture** : c'est la seule garantie que l'aperçu et l'export entendent
   la même chose. Le digest de bake 50 scènes ne doit pas bouger d'un octet.
2. **`Editor` sait déjà tout.** `sceneBuilt()` garde un `Core _scene` en mémoire, avec
   les mêmes `_inputs` que le compilateur. Nouveau `Q_INVOKABLE` dans
   `src/window/Editor.cpp` : construire la commande avec un input 0 factice
   (`-f lavfi -t <durée> -i nullsrc`) pour que les indices `[1:a]`, `[2:a]` restent
   identiques, `-map "[aout]" -c:a pcm_s16le` vers un WAV temporaire, lancé par un
   `QProcess` calqué sur `_export` (lignes 1206+). **Toute la timeline, en temps absolu :
   jamais `markIn/markOut` dans le WAV** — même raisonnement que A7, la lecture d'une
   plage devient un simple seek et coûte zéro re-mix.
3. **Le cache est la chaîne de filtre elle-même.** Hacher la commande produite : elle
   *est* la description exacte de l'audio de la scène. Inchangée après un `⌘R` → on
   garde le WAV. Sans ça, chaque exécution relance ffmpeg pour rien.
4. **`VC::Audio` à côté de `VC::nameApplication`** : `load(path)`, `play(double)`,
   `pause()`, `seek(double)`, `position()`. Cinq fonctions, un `AVAudioPlayer` statique
   dans `MacApplication.mm`, cinq `return false/0` dans `MacApplicationStub.cpp`.
   Linux sort en silence à la démo — dit à voix haute, pas découvert sur scène.
5. **QML — c'est ici que se joue l'architecture, et ça tient en trois lignes.**
   Le `Timer` de `Main.qml:3249` avance `playhead += 1/execFps`. Le commentaire au-dessus
   admet déjà le défaut : *« chasing real time would mean claiming a frame rate the pane
   is not delivering »*. Avec du son, ce n'est plus un défaut de goût, c'est une dérive
   audible qui grandit sans borne. **`onTriggered` lit `Shell.audioPosition()`** ; le
   `Timer` ne devient qu'un plafond de rafraîchissement. Fallback sur l'incrément
   image quand la scène est muette ou que le WAV n'est pas prêt.

## Ce qui casse

- Aperçu plus lent que le temps réel : l'image saute des frames. **C'est le
  comportement correct** et celui de tous les NLE ; un film à 0,6× synchrone ne l'est pas.
- WAV pas prêt au premier Espace après une édition : jouer muet, charger et seek à
  l'arrivée. Ne jamais bloquer le thread GUI en attendant ffmpeg.
- Scrub : pas de son (playhead maître, audio en pause). Ne tentez pas le jog audio ce soir.
- `volumeExpression` fait frames × inputs appels à `getMetadata` sur le thread GUI —
  9000 frames pour 5 min, acceptable, mais à mesurer avant de le croire.

## À terme

**Le pré-mix reste** — ce n'est pas un pis-aller. Les revendications sont connues
d'avance, il n'y a aucune entrée live : un graphe libavfilter temps réel dupliquerait
la chaîne de l'export et la parité pourrirait en trois mois. Les deux vraies évolutions,
toutes deux **derrière les mêmes cinq fonctions, donc sans toucher au QML** :
`avfilter`/`swresample` en process (déjà liés) pour tuer le spawn et re-mixer seulement
la région modifiée ; puis un ring buffer + `AudioQueue` pour le jog audio et la vitesse.
**L'audio est l'horloge maître dès qu'il y a du son ; l'image est maître au scrub.**
