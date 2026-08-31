# Editor UI — decisions and backlog

Companion to `editor.html` (the zoning mockup). What is settled, what is
deliberately postponed, and what the mockup still gets wrong. Nothing here is
implemented yet.

## Settled: the scene is a buffer, not a file

The scene source lives in the editor — an integrated console/source panel — and
is only written to disk on save. No file is touched behind the user's back, and
no file watcher is needed: a gesture mutates the buffer and the buffer is
recompiled.

`videocode/serialize.py:61` already does everything but this: `execScene(path)`
opens the file, `compile()`s it, `exec`s it, and C++ reads `Context.stack`
straight out of the interpreter (`src/core/Core.cpp:107`). Split it into
`execSource(content, name)` plus an `execScene(path)` wrapper and the buffer is
the source of truth with no other plumbing.

Consequences: editing the same scene in an external editor while the GUI is
open is no longer a supported workflow — on save, a file that changed underneath
is a conflict to report, not to merge. And since unsaved work exists only in
memory, the buffer needs a journal on disk to survive a crash.

## Settled: a gesture is an edit to the scene source

The source buffer is the only state. There is no separate GUI document, so there
is nothing to keep in sync — the timeline is a *view* of the source, and every
mouse gesture is a small rewrite of it.

1. **One gesture, one write, on release.** A drag paints its preview in the GUI
   and writes nothing. Mouse-up produces exactly one write. No write per
   mouse-move.
2. **Surgical writes.** A gesture changes only the argument it means. The file
   is edited through a CST round-trip that preserves comments, blank lines and
   formatting (`libcst`-style, not `ast.unparse`). The editor never reformats a
   file it did not have to touch.
3. **Anchors are AST nodes, not line numbers.** A clip remembers *which call*
   it came from (binding name + call-site index), so a gesture still lands
   after the file has shifted by ten lines.
4. **Computed clips are read-only.** If a clip's position comes from an
   expression rather than a literal — `for beat in sound.beats(): …`, an
   `f(x)`, a comprehension — dragging it is refused, with the reason shown. The
   editor never rewrites a loop to hard-code what the loop computed.
5. **Undo is the buffer's history.** `Ctrl+Z` pops one write off a stack of
   reverse patches and recompiles. One history for the whole app: a timeline
   drag and a keystroke in the source panel land in the same stack, because they
   are the same kind of event.
6. **Save is the only write to disk**, and it writes the buffer as-is.

## Settled: export has no GUI cost

Rendering from the editor must be exactly as fast as rendering from the CLI.
The GUI does not own a render path: it runs the same binary with the same
arguments (the command already shown in Settings → Render) and reads its
progress off stdout. No preview-quality path, no re-encode, no second
implementation to keep honest.

## Settled: one Qt, QML for the chrome

The UI is described in `.qml`, loaded from disk in dev builds (so a layout tweak
costs a reload, not a rebuild) and from `qrc` in release. No JSON layout schema —
QML already is the declarative layer, and a second one would only duplicate it.
No PySide6: it ships its own Qt and would collide with the static vcpkg Qt. One
Qt in one process.

To do: add `qtdeclarative` to `vcpkg.json` (today only `qtbase` with
gui/widgets/opengl) and `Qt6::Quick` to the `find_package` components in
`CMakeLists.txt:106`.

Quick runs on the **platform default — Metal on macOS — not on Vulkan**. Sharing
one graphics API with the renderer was the better idea on paper; the measurement
killed it. Same scripted run, same machine:

| | Vulkan (MoltenVK) | Metal |
|---|---|---|
| Wall time | 16.8 s | 4.5 s |
| `blockedForSync` per frame | 5012 ms | 0 ms |
| "Timed out waiting for display lock" | 3 | 0 |

A five-second stall of the GUI thread per frame is not a trade-off, it is an
unusable window — and it presents as "no button does anything", because clicks
arrive while the UI thread is blocked. `QSG_RHI_BACKEND` still overrides the
default, so the Vulkan path can be re-measured when MoltenVK or Qt moves.

That reopens how the preview gets into the chrome, and in a *better* place than
the underlay plan. With Quick on Metal there is no shared Vulkan command buffer to
record into — but MoltenVK backs every `VkImage` with an `MTLTexture`
(`vkGetMTLTextureMVK`), so the renderer can draw **offscreen** and hand Quick the
underlying Metal texture with no copy. And offscreen is what
`VulkanHeadlessRenderer` already does for `--generate`: the editor preview may not
need the on-screen `VulkanWidget` path at all, which would leave its swapchain
ownership untouched instead of refactoring it.

Second invariant that the editor breaks on purpose: `Window.cpp:71-85` refuses to
create a status bar and pins the widget to a scaled multiple of the video
resolution, so the swapchain extent stays a clean multiple. In a docked editor
the preview is one pane among several and cannot keep that property — it becomes
a letterboxed sub-rect, and the "clean multiple" reasoning moves to the render
path, which does not go through the widget at all.

## What a static Qt costs the chrome

Three consequences, all found by running it rather than by reading about it:

- **QML modules are static libraries.** There is no plugin to discover at runtime,
  so `import QtQuick` dies with "plugin qtquick2plugin not found" unless the
  plugin and its `_init` object are linked in. `qt_import_qml_plugins()` cannot
  help: it scans a target's own `.qml` files and ours are read from disk. The list
  is therefore explicit in `CMakeLists.txt` — extend it when a panel reaches for a
  module that is not in it yet.
- **The `qml` runtime tool is useless here** for the same reason, which removes the
  fast "preview the chrome without building" loop. Iteration goes through
  `./video-code --editor`, whose file watcher reloads the chrome on save, plus
  `qmllint -I qml qml/VideoCode/*.qml` for the static pass.
- **This Qt has no PNG writer** (`png` is not among the enabled qtbase features):
  `QImage::save` can only produce bmp/ppm/xbm. `--screenshot` therefore hands the
  grab to OpenCV through `VC::ImageIO`, the same path the preview window's frame
  export already uses. Enabling the `png` feature would mean another qtbase
  rebuild for one encoder the project already links.

`qmllint` is worth a CI gate next to the formatting one: it is fast, needs no
display, and it caught a genuine bug — `id: clip` on a timeline bar resolved to
`Item.clip`, the boolean property, so the waveform bars were sizing themselves off
`true`. What it does NOT catch is `font.pixelSize: 11.5`; pixelSize is an integer
and the engine rejects the fractional sizes the CSS mockup uses freely.

## The right-hand column is the agent

Properties and Effects are gone from the dock. Talking to the agent is not an
interruption of editing here — what it answers with is code, and the code is the
scene — so the conversation gets a permanent column instead of a drawer that
covers the dock. Permanent means permanent: there is no button to hide it. A
toggle in the title bar only invited people to close the column and then wonder
where the agent went, and a pane that is sometimes there is a pane you never
build a habit around. If it has to become hideable, it belongs to the dock's own
slot menu (`⋯`), with the other split/close gestures — not to the title bar.

The code panel is a tab in that same slot rather than a second layout — see
below: `Code` over `Agent` is just the state the dock opens in, not a wired-in
special case. `Edit`/`Code` layout presets are gone with it.

`PropertiesPanel.qml` and `EffectsPanel.qml` are kept on disk, unmounted. Their
home is the focus card — the view you get by clicking an element, where its
parameters and its effects belong. Nothing mounts them today.

## Settled: the dock is a tree, the way OBS's is

OBS gets its docking from Qt Widgets for free — `QMainWindow` plus `QDockWidget`
does the dragging, the tabbing, the floating and `saveState()`. Qt Quick has no
equivalent, so the same behaviours are written out here, in `Main.qml` (the
model), `DockNode.qml` (the tree, drawn) and `Panel.qml` (one slot).

The model is a tree: a node is either a **slot** holding tab keys or a **split**
holding more nodes. Every gesture is one edit to it, and the tree is replaced
rather than mutated, because a QML binding does not hear a `push()` three levels
down inside a `var`.

| Gesture | What it does to the tree |
|---|---|
| Drop a tab on a strip, or in a slot's middle | the slot gains a key |
| Drop it within a quarter of a slot's edge | that slot is replaced by a split of two |
| Drop it outside every slot | it leaves the tree for the `floats` list, and a `Window` |
| Close a tab (`×`), or close a floating window | the key is dropped; an emptied slot is pruned and a split of one collapses into its child |
| `⋯` → a panel's name | the panel is closed, or comes back in the slot whose menu you opened |
| `⋯` → Reset UI | the default tree, and the saved file deleted |

Four things this got wrong before they were measured, all worth keeping:

- **QML refuses a component that instantiates itself** ("DockNode is
  instantiated recursively") — it cannot bound the recursion at compile time. A
  `Loader` with a URL defers that to run time. The node must go in through
  `setSource()`'s initial properties, not `onLoaded`: `onLoaded` arrives after
  the child's `Component.onCompleted`, so the child would register itself as
  nothing.
- **Sizes live in two places.** The tree holds the fractions the layout was built
  with; `SplitView` writes the ones the user dragged into the items. Saving reads
  them back off the items, or every session reopens with the panes it was born
  with. Fractions, never pixels — a dock saved on a monitor has to reopen on a
  laptop.
- **A dying node must not erase a live one.** Rebuilding the tree destroys the old
  items *after* the new ones exist, so `forgetNode` only deletes the registry
  entry if it still points at the item that is going.
- **Drop positions travel in global coordinates.** A scene position means nothing
  to a floating panel in another window.
- **A `TapHandler` beside a `DragHandler` on the same item loses.** It is the
  pairing the handler documentation suggests, and it silently cost the tabs their
  clicks: the DragHandler took the exclusive grab on press, `onTapped` never
  fired, and dragging kept working — so nothing looked broken. `gesturePolicy:
  ReleaseWithinBounds` did not fix it either. One `MouseArea` that measures the
  travel itself and decides between select and move has no arbitration to lose.
  Worth remembering before reaching for handlers again on anything draggable.
- **The topmost item wins, not the smallest.** The tab's own MouseArea is
  declared after the `×`, which put it *above* the close target and swallowed
  every click meant for it. The `×` carries `z: 1` for that reason.

Not taken from OBS: **Lock UI**, and dragging a dock by its *title bar* rather
than by its tab (this dock follows VS Code and Blender there — the tab is the
thing that names the panel, so it is the thing to grab). The layout is written to
`QStandardPaths::AppConfigLocation/dock.json` by the shell, since QML cannot
write a file; anything in it that this build does not recognise is dropped rather
than trusted.

`VC_DRAG="x1,y1,x2,y2"` drives one drag and `VC_CLICK` now takes a sequence of
points, which is what makes any of the above checkable without a hand on the
mouse — a menu needs two clicks to prove anything. Both take **logical**
coordinates (the window is 1470×891 on a 2940×1782 screenshot), and the layout
they aim at depends on the saved `dock.json`: delete it first, or the numbers
from the last run point somewhere else.

## Settled: arrangements are named, and there are three

The dock tree is free-form, but nobody rebuilds a workspace by hand every time
the task changes. A **template** is a whole arrangement with a name, chosen from
`View → Layout` or with ⌘1/⌘2/⌘3, because switching is something you do
mid-thought and a menu you have to open for it is a menu you stop using.

| Template | Shape | For |
|---|---|---|
| **Normal Editing** | Media \| Preview over Timeline \| Agent+Code | the everyday one |
| **Vibe Coding/Editing** | Preview top-left taking only what a 16:9 frame needs, Media (as a list) and Timeline sharing the row beneath, the whole right column the conversation | talking to the agent, where what it answers with needs room to be read |
| **Preview** | The picture, and a strip of timeline to scrub it | watching, not editing |

The keys are `edit` / `agent` / `preview` — a saved layout names them — but the
labels say what you are about to *do*, not which panel is biggest. A key this
build no longer has (`code` was one) falls back to the everyday arrangement
rather than leaving the menu with nothing ticked.

Two sizing rules came out of using it. **A pane taller than its picture is dead
space you cannot use**, and it is stolen from the panes that grow usefully — so
the preview's share is close to what its aspect actually needs and no more.
And **a pane too small to use is worse than one that is not there**: the Preview
template closes the bin, the buffer and the conversation instead of shrinking
them to slivers.

Beyond the three, an arrangement can be **named and kept**: `Save display…`
snapshots the tree, the floating windows and the panel options under a name, and
`Load display` brings it back exactly as it was. Saved displays live under keys
of the form `user:<name>`, so everything that already worked per template —
remembering your edits, resetting, the window title — works for them unchanged.

`Reset UI` asks first, in a centred modal, and offers **Save it first…** in the
same breath. Everything else in this chrome is a menu that closes when you look
away, which is right for a choice you can take back by making it again and wrong
for one that throws away an afternoon's arrangement.

The window title is the template's name. Which arrangement you are in is the one
thing a title bar can say that the window does not already show.

This is not the `Edit`/`Code` preset pair that was removed earlier, and the
difference is the point: a preset *replaced* your arrangement, so there was no
reason to touch it twice. A template is a starting shape you then bend, and
**your version of each is kept separately** — floating panels included, since a
window torn off belongs to an arrangement as much as a pane does. Switching away
saves what you did; coming back gives it to you, not the factory shape. `Reset
UI` resets only the template you are in, because losing the two you are not
looking at is never what you meant.

Ids are prefixed per template (`a-stage`, `e-side`, `c-code`) so two
arrangements cannot argue over one name in the node registry while one is
replacing the other.

A template carries more than a shape: **panel options travel with it**. The bin
opens as a details list in Code — where you are after the exact spelling of a
filename to type, not a thumbnail — and as a grid everywhere else, and changing
it from the slot's `⋯ → Display` changes it for the template you are in, not for
the application. That is the same reasoning as the arrangement itself: what you
want depends on what you are doing. `options` is a map next to `tree` and
`floats` in each saved template, so the next option to want a home has one.

The bin tints each row with its kind's hue instead of putting a dot in a column:
a dot is a legend you have to look up, a tinted row is read at a glance — and it
is why there is no KIND column either.

The bin's details columns are Name and **Used** — how many times the asset
appears in the edit. Used is the only extra column this model can fill honestly
(assets carry a name and a kind, nothing else), and it happens to answer the
question a bin is opened with: is this thing in the cut. The kind is the dot, and
only the dot: a word spelling out what the colour already says is a column of
noise.

Which puts weight on the palette being learnable, so `⋯ → Guide → Colours` shows
it: every swatch reads its value from `Theme`, so the legend cannot drift from
what the timeline paints. Opening it surfaced one thing worth deciding: the
effect complement for video (`#e08a3a`) sits close enough to the live accent
(`#f0703c`) that the two read as the same family — and the palette's own rule is
that the accent must always win.

## The menu bar is the platform's, not ours

Settings left the window. A Mac user looks for it in the menu bar at the top of
the screen, and a strip the application painted for itself is not that bar — so
this one control is Qt Widgets rather than QML: a `QMenuBar` with **no parent**
is the system-wide menu bar on macOS, and `QAction::PreferencesRole` moves the
item into the application menu beside About and Quit, with ⌘, attached.

Two things to know before adding to it:

- Qt Quick's own `MenuBar` draws a bar **inside** the window. On macOS that is
  the wrong answer whatever it looks like, which is why the chrome does not own
  this piece.
- Qt renames a `PreferencesRole` action to the platform's standard string: the
  item reads **Preferences…** on screen no matter what text it was given.

The menu it is added to (`video-code`) is never shown — macOS empties it by
relocating the action — so it is a hook, not a menu to fill. `Editor` emits
`settingsRequested()` when the item is chosen; nothing listens yet, because
there is no settings surface to open (the old in-window button did nothing
either). That signal is where one plugs in.

**Dock display** is the visible half of the bar: `Layout` picks the named
arrangement (⌘1/⌘2/⌘3), `Docks` ticks the five panels, and `Reset UI` restores
the current template's default shape. Named for what it holds rather than
borrowed from every other application — and `View` would have collided with the
slot menu's `Display`, which is about one panel rather than the whole window.

The application menu reads **Video-Code** when the `.app` is launched, from
`CFBundleName`. Run the bare executable and macOS uses the filename instead —
that name belongs to the process, not to Qt, and no API overrides it. Both are the same state the
slot's own `⋯` menu shows, deliberately — a panel that has been closed or dragged
somewhere silly has to be recoverable from a place that does not require finding
that panel first, which the `⋯` menu does.

The bar is Qt Widgets and knows nothing about the dock tree, so the chrome pushes
the list to it (`Shell.setDockPanels`) on every change and listens for
`dockPanelToggled` / `dockResetRequested` coming back. The submenu is rebuilt
rather than reconciled: five items cost nothing, and a menu that is rebuilt cannot
drift out of step with the dock.

## Settled: the buffer is coloured by C++, not by the chrome

Qt Quick has no syntax highlighter. A `TextArea` can be handed rich text, but
then every keystroke re-marks the whole buffer in JS and the cursor fights the
markup — an editor that stutters while you type is worse than one with no
colours. `QSyntaxHighlighter` re-highlights only the blocks that changed and
plugs into the `QTextDocument` that already backs the TextArea, so
`PythonHighlighter` does the work and the chrome only hands the document over:
`SourcePanel` emits `documentReady`, the shell attaches. The panel does not know
a highlighter exists.

- **The palette stays in `Theme.qml`** (`Theme.code`) and is passed in. The one
  file that owns colour keeps owning it, and the code panel cannot drift from the
  rest of the chrome.
- **The highlighter is parented to the document**, so it dies with the panel and
  a chrome reload leaves nothing behind. Attaching twice is refused by looking
  for an existing child of that type.
- **Strings and comments are painted after the rules, not as rules**: a keyword
  inside a string is not a keyword, and a `#` inside a string is not a comment.
  Triple-quoted strings span blocks, and the previous block's state is the only
  memory a highlighter has.

The panel around the colours is an editor too, not a text box: a **gutter with
line numbers** (a traceback from the compiled scene points at a line, and a
timeline gesture rewrites one — without numbers neither can be pointed at out
loud), a **current-line band**, **no wrapping** (a wrapped line lies about where
the line ends), and **Tab as four spaces**, since a stray tab in a Python buffer
is a syntax error waiting for the next editor to open the file. The gutter
follows the view rather than living inside it: one that scrolled sideways with
the text would stop being a gutter the first time a line ran long.

Two colourings are deliberate rather than conventional: keyword arguments
(`width=1.5`) get their own hue, because nearly every line of a scene is one;
and control flow is told apart from declaration, because *what this line does*
and *what this line is* are different questions.

## The timeline's two thefts, repaid

Both found by looking at a full window rather than at the panel on its own.

- **A name written over a waveform is unreadable**, and outlining it makes it
  worse: the outline fights the peaks it sits on and the eye has to work out
  which pixels are letter and which are audio. Every NLE that has to write over
  audio solves it the same way — a solid band along the top of the clip, in the
  clip's own hue, with the waveform starting underneath. Near-black text on the
  band, which beats white on every hue in this palette.
- **The zoom slider owned a 28 px strip across the whole panel** to hold one
  control you touch once a session, on the panel whose height *is* its
  usefulness: a lane you cannot see is an element you forget. It now rides the
  right-hand end of the ruler, which is a repeating scale — covering its last
  hundred pixels costs nothing, while covering a clip hides the one thing the
  panel exists to show.

## Not done: panes that do not fill the dock

Asked for: shrink a pane, let the window's background show through the gap, then
grow another pane into it later. The dock cannot do that today and it is not a
tuning job — `SplitView` distributes *all* of its space among its children by
construction, so a gap is not expressible.

Two ways to get there, in ascending order of damage:

1. **A `gap` node in the tree.** The model already has the shape: a node that
   renders as nothing but still takes a fraction and still has splitter handles
   on both sides. Shrinking a pane means growing the gap beside it; growing a
   pane means eating it. Cheap, and it keeps every other behaviour (saving,
   templates, drop zones) working unchanged. What needs deciding first is how a
   gap is *made* and *unmade* — a menu action, a drag past a minimum, or
   automatically when the last tab of a slot is closed (today that slot is
   pruned).
2. **Absolute panes with edge resizers**, dropping `SplitView` entirely. Truly
   free-form, and a rewrite of the layout half of the dock: sizes stop being
   fractions of a parent, so persistence, the templates and the drop geometry all
   change with it.

Worth doing as (1) if it is wanted; (2) is a different product decision.

## Two colour traps, both silent

- **`#RRGGBBAA` is CSS, `#AARRGGBB` is Qt.** The same eight characters mean two
  different colours and nothing warns you: `"#ffffff26"`, a faint white in the
  mockup, became opaque yellow in the chrome — clip outlines, media glyphs and the
  agent's avatar were all wrong. Translated colours now go through `Qt.rgba()`,
  which cannot be misread.
- **`font.pixelSize` is an integer.** The mockup's `11.5px` is legal CSS and makes
  the QML engine reject the whole component. `qmllint` does not catch either of
  these; only running it does.

## Settled: ⌘R is the only thing that executes the scene

The picture and the timeline do not follow your typing. They follow a key.

The reason is not speed — `execScene` is 2.6 ms on `scene.py` and 12.5 ms on
`eg.py`, both inside a frame. It is that a scene is arbitrary Python whose
constructors open files: a typing-pause cadence runs unfinished text ten to
thirty times a minute, and a compile gate does not save you, because `wait(1)`
mid-keystroke is `wait(11)` — syntactically perfect, semantically another film,
executed for real. **You can debounce a question; you cannot debounce a side
effect.**

What that costs is that the picture is behind the buffer, so the status strip
carries the state: a green pip and `ran 99 ms` when it matches, an amber
`stale — ⌘R` the moment the buffer moves, a red `scene failed — ⌘R` when the
last run threw. `guideColors()` had promised for months that warn means "stale —
the picture is behind the buffer"; this is the first thing that keeps it.

A failure leaves the last good run alone and lands as a diagnostic on the line
that raised it, in the same shape the language server's own diagnostics use — an
emptied timeline after a typo is the worst possible answer.

`⌘R` is in `Keymap` like every other key, so it is on the board and rebindable.
It is handled in the code pane's key handler **as well as** by a window
`Shortcut`: Qt matches a `Shortcut` from the platform's key handler, so a
synthetic event never reaches one, and the whole path would be untestable by the
scripted probes this project verifies everything with.

The scene executed is the **buffer**, through `serialize.execSource(text, path)`
— never the file. `path` is passed only so tracebacks and provenance point at
the file you are looking at.

## Settled: a restart forgets which tab you were on

Where the panes ARE survives closing the app. Which tab you happened to leave in
front does not, and neither does the order you dragged them into.

The line is between an arrangement and a glance. Moving a pane, splitting one,
resizing one — that is the shape of the room, and it was built on purpose.
Clicking Agent to read something is not: it is where you were looking a second
before you quit, and a tool that reopens on it has remembered the wrong half of
what you did.

So on restore, every slot of a **built-in** arrangement gets its opening order
back and its first tab in front. Slots are matched by id (`c-chat`, `a-stage`),
which are stable per arrangement, so a dock you have restructured keeps the
structure you gave it and only the recognisable slots are reset. Keys the
template does not know are kept, after the ones it does — nothing is dropped,
only sorted.

**A saved display is the opposite promise** and is untouched by this: it reopens
exactly as it was named, tab selection included. That is the whole difference
between a starting shape you bend and an arrangement you decided was worth
keeping.

The normalised layout is written back once on restore, so the file on disk says
what the window says rather than holding a stale index nobody obeys.

## Settled: a clip opens into a card, not into the timeline

Clicking a clip answers one question — *what is actually in there?* — and it
answers it **somewhere else**.

The card starts exactly where the clip is and travels to the middle of the
window, at a size you can read. That is not decoration: a panel that simply
appears has to be connected to what you clicked by an act of faith, and this one
shows the connection instead of claiming it.

What is inside a clip does not belong on the timeline. Rows that grow push
everything below them down, and a map whose geometry changes when you look at
something has stopped being a map.

A row made of several inputs from **one line** opens into its members —
`Text("GRADIENT")` is eight inputs, one per glyph, and `eg.py` is 36 for six
things. Rows are folded by call site, since the engine has no group to ask:
`Group` is an `Interface` and only its members reach C++. Parts are numbered
(`title 1`, `title 2`) because they all come from one line and eight rows called
`title` name nothing, and the row itself is part 1 — a word of eight letters that
reports seven is a bug you only notice by counting.

A row that is one input opens into **what happens to it**: one bar per effect,
drawn against the CLIP's length rather than the scene's, so an effect covering
the whole clip looks like it.

**A span is when the element is on screen, not when it has entries.** The
difference is the whole of the typewriter: it writes `opacity(0)` at frame 0 for
every letter before ramping each one in, so by key presence all eight glyphs
start together and the stagger — the point of the gesture — disappears.
Visibility is read from the VALUE, with the renderer's own predicate (not hidden,
opacity not zero). The eight letters then start at frames 0, 2, 5, 7, 10, 12, 14,
17, which is the cadence you asked for.

The class shown is the OUTERMOST library frame's — a `Text` builds `Letter`s, and
the letter is an implementation detail of the word.

**Adding an effect writes a line, never edits one.** `+ effect` on the card
lists what `videocode/template/effect/` actually exports — discovered at run
time, because a hand-written list is wrong the day someone adds a file — and
picking one inserts `square.apply(flash())`, plus the import it needs, since
effects are not part of `from videocode import *` and a call without its import
is a scene that does not run. An inserted statement can be read, moved and
deleted; rewriting an existing call is the thing three councils refused.

(An earlier version put that button in the timeline lane, where it was drawn past
the content's right edge — visible and unclickable, because Qt Quick clips input
to an item's geometry even when it does not clip painting.)

## Postponed, not forgotten

| Area | What is missing | Note |
|------|-----------------|------|
| Audio | Level meter, mute/solo affordance (`M` is bound to nothing visible), master gain | Explicitly later |
| Color | `lut()` exists in `videocode/shader/fragmentShader/lut.py` but the UI has no scopes (waveform, vectorscope) and Render has no colour-space field | Not handled by the engine yet either |
| Subtitles | `Sound.transcribe()` exists; no surface reads or re-times the text. The mockup's `subs` element kind has no matching input class | |
| Value over time | Properties shows static values; an effect is Start/Duration/Easing with no curve. For an animation-first tool, a property-over-time graph is the natural missing panel | |
| Composition order | One lane per element ordered by start time hides stacking. `zIndex` lives in Properties; `blend` and mattes have no timeline representation | Real tension in the timeline design |
| Export feedback | Progress, ETA, log, past renders — parsed from the binary's output (see above) | |
| Timeline furniture | Markers, in/out range, loop region, multi-select, vertical scroll past ~40 elements. **Appears only for the clicked element**, like effects | |
| `Sound.beats()` | `videocode/input/media/Sound.py:163` — spectral-flux onset detection returning `list[sec]`, plus `transcribe()` at :239. Neither is remembered being written; review whether they are wanted, tested and documented before any UI leans on them | Low priority, but do not build on it until reviewed |
| Chrome polish | The zoom `Slider` still wears the Basic style (pale track, oversized knob) — the one control that has not been given the chrome's own look | Small |
| Reproducible captures | `--screenshot` works, but the monospace face is `Menlo`, which exists only on macOS. A golden test needs a mono font bundled in `assets/fonts` and loaded by path, the way `Inter-Regular.ttf` already is | Blocks golden tests, nothing else |
| Clip ↔ source link | Reciprocal highlight (click a clip, the call that made it lights up in the code panel) is on-demand only — the timeline writes code in the background and does not advertise it | Low priority |

## Mockup fixes

`editor.html` is a zoning study, so these are cosmetic — but they should not
survive into the Qt6 port.

- **Invented API.** `cuts()` and `speedRamps` in `ELEMENTS` match nothing in
  `videocode/`. `beats()`, `transcribe()`, `fadeIn`, `fadeTo`, `kenBurns` and
  the whole effects library are real. Replace the two fakes with real calls.
- **Snap step is not a frame.** Snapping is 0.1 s, which never lands on a frame
  boundary at 30 fps (0.0333 s), while the viewer displays frames (`00:00:04:11`).
  Quantise to the frame.
- **Modifier mismatch.** The drag bypasses snapping with `metaKey` (⌘) but
  `ACTIONS` declares `Suspend snapping = Ctrl`, so the keyboard map lies.
- **Three time formats.** Ruler in `MM:SS`, viewer in `HH:MM:SS:FF`, effects in
  seconds with two decimals.
- **Placeholder count.** The effects filter says "47 effects"; the real count is
  whatever `videocode/template/effect/` plus `videocode/shader/fragmentShader/`
  export.
