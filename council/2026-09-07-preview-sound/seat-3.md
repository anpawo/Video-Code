# Siège 3 — Le son de l'aperçu

**Ferme : pré-mixer un WAV avec *exactement* la chaîne ffmpeg du rendu, le jouer avec miniaudio
(un header), l'audio horloge maître.** Pas de qtmultimedia (rebuild vcpkg + `Q_IMPORT_PLUGIN`
sur Qt statique la veille d'une démo). Pas de `ffplay -nodisp` : il ne sait pas dire où il en
est — dérive non bornée, pause = tuer le process.

## Qui est l'horloge (le point qui décide de tout)

Le Timer de `Main.qml:3243` **compte des images** (`playhead + 1/execFps`) — assumé tant qu'il
n'y a pas de son. Avec du son c'est le bug : le son avance en temps réel, l'image en temps de
rendu, une pane qui rame joue au ralenti sur une bande normale. **L'audio devient le maître et
l'image saute des images**, ce que fait tout lecteur. Sans piste sonore : le compteur actuel.

## La nuit (ordre exact)

1. **Sortir le mixeur de l'anonyme.** `src/compiler/Compiler.cpp` L31–231 (`hasAudioStream`,
   `videoAudioChain`, `volumeExpression`, `buildAudioArgs`) → `include/compiler/AudioMix.hpp`
   + `src/compiler/AudioMix.cpp`, `namespace VC::Audio`, plus deux paramètres : `firstInput`
   (1 au rendu où la vidéo est l'entrée 0, **0** à l'aperçu) et `mapVideo` (retire
   ` -map 0:v`). Rien d'autre. **Un second mixage = un aperçu qui ment : non négociable.**
2. **Pré-mix côté éditeur.** `src/window/Editor.cpp`, après `sceneBuilt()` (L~1180) :
   `VC::Audio::buildAudioArgs(_scene->_inputs, "pcm_s16le", std::nullopt, _scene->_nbFrame, 0, false)`
   → `ffmpeg -y -loglevel error {inputs} -filter_complex "{filter}" -map "[aout]" -ar 48000 -ac 2 <tmp>.wav`
   en `QProcess` (pattern `startExport` L1206). **`window = nullopt`** : WAV en temps timeline
   absolu, donc `seek(t)` = `t`. Cache = hash de la commande (qui encode déjà delay, trim,
   volume, chaque rampe) + mtime des fichiers → un rebuild par frappe reste gratuit.
3. **Le lecteur.** `miniaudio.h` vendoré (domaine public, un fichier ; CoreAudio + ALSA/Pulse
   en `dlopen`, rien à installer sous Linux ; sous macOS ajouter `AudioToolbox`, `CoreAudio`,
   `CoreFoundation` au bloc `APPLE`, `CMakeLists.txt` L230–252). `ma_engine_init` une fois,
   `ma_sound_init_from_file(..., MA_SOUND_FLAG_DECODE, ...)` → décodé en RAM (3 min stéréo
   ≈ 33 Mo), seek instantané. Quatre `Q_INVOKABLE` sur `Editor` — `audioPlay(double at)`,
   `audioPause()`, `audioSeek(double)`, `audioPosition()` (`-1` si muet) ⇒ `ma_sound_start/stop`,
   `ma_sound_seek_to_pcm_frame`, `ma_sound_get_cursor_in_seconds`.
4. **QML.** `togglePlay()` (L3226) appelle `audioPlay(playhead)` / `audioPause()` ; le Timer
   (L3249) devient : `const p = Editor.audioPosition(); playhead = p < 0 ? playhead + 1/execFps : Math.max(playhead, p)`
   avec l'arrêt sur `until` inchangé. `onSeek` (L3378/3417) coupe déjà la lecture → `audioSeek`.
5. **Vérif sans fenêtre.** Un test comparant le `filter_complex` du rendu et celui de l'aperçu
   sur une scène à 2 `Sound` + `duck` : identiques aux indices d'entrée près. Puis
   `--check-chrome`, et une écoute du WAV contre l'audio du `.mp4` — seul juge du reste.

## Ce qui peut casser

- **Latence** : le curseur miniaudio est celui de lecture, pas ce qui sort du HP — l'image passe
  ~1 image en avance. Laisser une constante d'offset réglable, défaut 0.
- **Démarrage** : `ma_sound_start` n'est pas instantané, d'où le `Math.max` — sinon le
  playhead recule à 0 à la première tick. **`amix duration=longest`** : le WAV peut dépasser
  la scène, on coupe sur `until`.
- **Vitesse ≠ 1** : `ma_sound_set_pitch` transpose (voix de canard) → son coupé hors 1×, dit à
  voix haute. **Pas de son au scrub** non plus : voulu. Le son d'un `Video` arrive gratuitement
  (`videoAudioChain` est dans le même mixeur).

## À terme

**Ce n'est pas un provisoire.** Tant que la loi du mixage vit dans des filtres ffmpeg, le
pré-mix est la bonne forme. Le vrai temps réel (décodage libav\* par source, revendications
appliquées dans le callback, somme dans un `ma_device`) n'achète que la réponse instantanée à
une édition, le son au scrub, la vitesse propre : à payer quand le re-mix gêne *mesurablement*.
Survivent tels quels : `VC::Audio` partagé, l'audio horloge maître, les quatre appels de
`Editor` ; seul `ma_sound_init_from_file` est remplacé — d'où la règle : **cette API ressemble
à un lecteur, jamais à un fichier.**
