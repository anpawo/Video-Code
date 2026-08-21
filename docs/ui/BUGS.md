# Known bugs and gaps in the editor

Found by the councils of 2026-08-15 and 2026-08-16 and by reading the code since. Kept here so
none of it is rediscovered twice. **Fixed entries stay, struck through, with the date** — a list
that only shows what is broken teaches nothing about what was.

Councils: `~/.claude/councils/2026-08-15-videocode-code-timeline-preview/`,
`~/.claude/councils/2026-08-16-videocode-group-rows-and-execute/`,
`~/.claude/councils/2026-08-16-videocode-unknowns/`.

---

## No known answer yet

**A scene spread over several files.** "The buffer is the truth" is a single-file invariant.
`app.scenePath` names one file; a helper module edited in the pane is invisible to a re-execute,
invisible to provenance, and Python's module cache means an edited `helpers.py` is not even
re-imported without `importlib.reload`. Forces a choice: either the scene is *the file* and
helpers only count once saved (the editor then lies about one of the two), or an open-buffer set
with an import hook, which drags reload semantics into every run.

**Two evaluators of one buffer** *(much smaller since the namespace fix — an in-process run and
a fresh process now differ only in `sys.modules` and in C++ state that `reloadSourceFile()`
rebuilds).* `docs/ui/BACKLOG.md` commits export to re-running the binary,
while an execute key would run the scene in-process. The same scene then runs in two places — one
interpreter alive all session, one fresh — and they can disagree. Same root as the first entry,
at the level of the architecture.

**Audio, end to end.** `Compiler.cpp::buildAudioArgs` hands `-i`/`amix` to ffmpeg; the engine
never decodes a sample. `TimelinePanel.qml:228` draws a deterministic pseudo-waveform from an
index hash. There is no playback path and no real-time clock for audio to slave to — and the
preview design (render on demand into a texture) does not provide one. *Deferred by decision.*

## Known answer, not yet chosen or built

**A crash takes the unsaved buffer with it.** No autosave, no recovery. Today the shell executes
nothing, so this is theoretical; an execute key makes it reachable by a keypress. The fix is not
mysterious — write the buffer to a sidecar on a timer and on every execute, and offer recovery at
launch when the sidecar is newer than the file. A crash cannot be prevented; the loss can.

## Wrong today, and cheap

- **A scene reports one frame more than it renders.** (2026-08-21) `serialize.sceneModel` returns
  `frames = Context.lastEverAffectedFrame + 1`, but that cursor is already EXCLUSIVE — it points at
  the frame after the last one carrying anything, so it IS the count. Measured on `scene.py`: the
  content is frames 0→80, the renderer writes 81 frames (`ffprobe` agrees, and the generator's own
  banner says `2.7s · 81 frames`), and the timeline draws 82 — 2.733 s of scene for a 2.700 s
  video. The C++ side reads `lastEverAffectedFrame` raw and is right; the `+ 1` is Python's alone,
  in two places (`serialize.py:122` and `:422`).
  Found by drawing `wait()`s across the timeline: the last band stopped one frame short of the
  clips, and the first answer — extending a trailing gap to the scene's end — was a special case
  papering over a global off-by-one. Not fixed yet because removing it shortens every rendered
  video by one frame, which is a decision about output, not about the editor.
- **The media bin is not persisted.** A dropped file now becomes a line of code — which survives,
  because the buffer does — but `addedAssets` itself is still lost on a chrome reload.
- **`scenePath()` recomputes on every call**, so the scene could never be changed at run time.
  *(Worked around by `app.scenePath` now being assigned on open; the C++ side still recomputes.)*
- **The scene file on disk is never re-read.** Nothing watches it the way `_watcher` watches
  `qml/*.qml`, so an edit made outside the editor is clobbered by ⌘S. *Judged not worth fixing:
  nobody edits the same file in two places.*

## Fixed

- ~~**Space did not play, and the pointer blinked out.**~~ (2026-08-18) The transport's five keys —
  Space, ←, →, Home, End — were global `Shortcut`s, and the code pane has the caret from startup.
  `TextEdit` claims those keys through `ShortcutOverride`, so the shortcut never fired AND the space
  still landed in the buffer: nothing played, the scene went quietly stale, and macOS hid the mouse
  pointer the way it does for any keystroke, which is the blink. They now belong to whichever of the
  two has the caret: clicking the picture or the timeline takes it out of the pane and the transport
  gets its keys back. Verified: Space at boot leaves the playhead at 0; a click on the picture then
  Space reaches 00:00:02:30. The board says so too, in a sentence derived from `Keymap` rather than
  written beside it.

- ~~**A short scene drew a sliver of timeline.**~~ (2026-08-18) Two seconds at 80 px/s is 160 px of
  content in 1400 px of panel, which reads as a timeline that has been cut off rather than a video
  that is short. The zoom now has a floor — a scene is drawn at least a third of the panel wide —
  set as the slider's `from` rather than as a clamp over it, so the handle and the picture cannot
  disagree and no part of the slider's travel does nothing. Measured: `scene.py` went from 80 px/s
  to 176 px/s, filling a third exactly.

- ~~**The timeline was about someone else's video.**~~ (2026-08-18) `PlaceholderScene.qml` — five
  invented clips called `interview.mp4`, `music.wav`, `logo.svg` — was still the fallback, so a
  freshly opened `scene.py` was represented by a stand-in, and the preview beside it said
  `⌘R to run the scene`: three panels telling three different stories about the same file. The
  file's own header said *"Delete this file the day Editor.cpp registers the real model"*; that day
  had passed. Opening a scene now executes it, so the timeline and the picture are about the buffer
  from the first second — the rule that they only move on ⌘R was about EDITS, to stop the picture
  flickering under your typing, and was never meant to leave an opened file represented by nothing.
  The media bin comes from the same place: the `Video`, `Image` and `Sound` inputs the scene
  actually loads, plus what was dropped this session. With no scene, the timeline says so.

- ~~**The preview was a dark rectangle.**~~ (2026-08-17) `PreviewItem` renders the current frame
  with the engine that `--generate` uses — a `VulkanHeadlessRenderer` owned by `VC::Editor`,
  headless at PANE size — and hands it to the scene graph as a `QSGSimpleTextureNode`. The frame
  is produced in `updatePolish()`, on the GUI thread: `updatePaintNode` runs on the render thread,
  and `Core` holds live `py::dict`s in a codebase that has never touched the GIL. `executeScene`
  builds the scene in the same call that runs the buffer, so the picture and the timeline can
  never be looking at two different executions. Verified: `scene.py` at frame 0 draws the blue
  square and the red circle on the engine's (51,51,51); `eg.py` scrubbed to ~3.7 s differs from
  frame 0 in 312 573 pixels — the gradient has swept the title, the bar has filled, the star
  fields have moved. `--visual-test` unchanged (only the three entries in
  `test/visual/known_failures.txt`).

  **This also answers an unknown**: two graphics devices — MoltenVK headless and Quick's Metal —
  coexist in one process without trouble.

- ~~**The transport moved nothing.**~~ (2026-08-17) `playing` was a flag no clock read, and the
  timeline had no way to place the playhead at all — `scrubbed()` was declared and never emitted.
  Playback is now a frame clock (one frame per tick at the scene's fps, not a wall clock: frames
  are rendered on demand on this thread, and chasing real time would mean claiming a rate the pane
  is not delivering), and the RULER scrubs on press and on drag. The ruler only: a click on a clip
  means "open this", and one gesture that does two things depending on where it lands is a surface
  you stop trusting.

- ~~**Switching tabs shrank the pane, a little more each time.**~~ (2026-08-17) `captureSizes`
  normalised each pane's extent over the SUM of its siblings, while `DockNode` applies the
  fraction to the split's full width — the two differ by the splitter handles. Every capture
  therefore inflated each pane by its share of a handle, SplitView clamped the total, and the
  last pane absorbed the loss. Measured: four Agent↔Code switches moved a 50/50 split to
  51.1/48.9, and it kept going. Now measured against the split's own extent, so a capture
  reproduces the pixels it read: verified stable at 50/50 and at 70/30 over twelve switches.

- ~~**The timeline read a mock.**~~ (2026-08-17) It is built from what ⌘R actually made:
  `serialize.sceneModel()` returns each element with its call site, kind, span and effect runs;
  rows are folded by call site; the label is the variable name read off the line that made it.
  `PlaceholderScene.qml` is still the fallback before the first run.

- ~~**Nothing in the editor ran the scene.**~~ (2026-08-16) ⌘R executes the **buffer** through
  `serialize.execSource(text, path)` in the embedded interpreter, reports `{ok, ms, line, column,
  message, inputs, frames}`, shows a failure as a diagnostic on the raising line, and drives a
  status-strip state: green `ran 99 ms`, amber `stale — ⌘R`, red `scene failed — ⌘R`. Decision in
  `docs/ui/BACKLOG.md`.

- ~~**The interpreter kept state between runs.**~~ (2026-08-16) `execScene` executed into
  `globals()`, so every name a scene bound survived the next run and the editor's picture drifted
  from what `--generate` renders. Each run now gets a fresh `dict(globals())`. Measured cost:
  none — 2.5 vs 2.6 ms on `scene.py`, 12.4 vs 12.7 on `eg.py`, 231.8 vs 230.0 on the stress
  scene, seven runs each, all inside noise. Decision:
  `~/.claude/councils/2026-08-16-videocode-process-architecture/log.md`.
- ~~**The code pane had no keyboard focus at startup.**~~ (2026-08-16) `load()` asked for focus
  before the item was laid out and the request was lost, so ⌘S, F12 and ⌃Space did nothing until
  you clicked in the pane. Asked again once the tree has settled.
- ~~**⌘S outside the project was a silent no-op.**~~ (2026-08-16) The pane now knows a file is
  not writable before you type (`Shell.writable`), and a refused save says so.
- ~~**Transport keys bypassed `Keymap`.**~~ (2026-08-16) Play, start, end, previous and next
  frame are actions like the others: on the board, and rebindable.
- ~~**One `dock.json` for every project.**~~ (2026-08-16) The file is now
  `dock-<folder>-<hash>.json`, and an existing `dock.json` is adopted once rather than lost.
- ~~**A dropped file did nothing.**~~ (2026-08-16) A `DropArea` over the window turns a video,
  image or sound into a statement at the caret — `test = Video("test.mp4")`, path relative to the
  project — and a row in the bin. An insertion, never a rewrite.
- ~~**A letter could not be sent by the scripted probe.**~~ (2026-08-16) `VC_KEYS` only knew
  named keys, so `Ctrl+S` failed with "no key named S" and every letter shortcut was untestable.
- ~~**Semantic tokens from the previous file painted onto the next one.**~~ (2026-08-16) The
  highlighter keeps spans by line and column, and nothing cleared them when the buffer was
  swapped — so opening `eg.py` after `scene.py` painted `ocode ` teal, because `scene.py` had a
  class at line 4, column 9. Cleared on open, and re-requested.
- ~~**The code tab always read `Code`.**~~ (2026-08-16) `source.name` and `source.modified` were
  set and read nowhere; the tab now reads `Code (scene.py •)` while it is the current tab of its
  slot, and plain `Code` when it is behind another.
- ~~**No way to open a scene.**~~ (2026-08-16) File → Open Scene… (⌘O) and Open Folder… (⇧⌘O);
  the folder also re-roots the language server, which needs a new process because a server's root
  is fixed at initialize.
- ~~**A menu filled only at construction never appears.**~~ (2026-08-16) Qt's Cocoa bridge
  inserts a menu when its contents *change*; File was populated in `buildMenuBar()` and therefore
  never inserted. Filled on the first tick of the event loop instead — which is also what fixes
  its position, since the bar's order is the order menus are filled.
- ~~**A group's chained transforms jumped, and only in one writing order.**~~ (2026-08-20) Not the
  editor — the library. A member's position on a `Group` depends on the group's position AND
  rotation AND scale at that frame, and each transform emitted its frames as it was written:
  `rotateBy(180, duration=1.5).scaleTo(0.5, duration=0.5)` laid down 45 frames of orbit at scale 1,
  and the scale pass only corrected the 15 it covered. The members shrank for half a second and
  then jumped back out to twice the radius in one frame. Written the other way round it was fine —
  the later pass read the earlier one's per-frame record, and beyond that window `meta` happened to
  hold the right value — which is why `video.py`'s showcase never caught it: it uses the working
  order with two equal durations, under a caption that shows the broken one. `Group` now records
  the window and writes it once per call, each frame carrying the state that holds AT it. Guarded
  by `test/group_test.py`, which asserts the two orders produce the same animation.
- ~~**Following a definition and coming back corrupted the analyser's copy.**~~ (2026-08-15)
  `load()` assigned the text before the path, so the change signal fired while `path` still named
  the file being left; the shell told the server that `scene.py` contained `Rectangle.py`. One
  round trip produced 62 phantom diagnostics.

## Not investigated

Two council seats stalled before reporting. These questions are open, not clear:
determinism (randomness, time, iteration order, float accumulation across reload); the case where
`_pySnapshot` says "unchanged" but the source changed; whether rendering at pane size differs
from the final render for anything resolution-dependent; C++ state surviving a reload (an open
`cv::VideoCapture`); **the unstoppable scene** (`while True:` on the GUI thread, with no GIL
discipline anywhere); the language server having no timeout,
restart or backpressure; growth over a long session (`_versions`, `_pending`, `_tokenRequests`,
`nodeItems`, thumbnails, the mesh cache); a truncated `dock.json` at startup.
