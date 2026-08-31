# Video-Code — what the application can do

Video-Code renders videos from Python. A scene is a `.py` file: you name shapes,
images, sounds and video clips, you say what they do, and the engine draws every
frame with Vulkan.

There are two ways to run it — a command line that renders, and an editing shell
that lets you write and watch at once. This page is the whole of both. For the
Python API itself — every shape, effect, shader and transformation — see
[`docs/FEATURES.md`](../FEATURES.md).

**One rule this page keeps:** where something is a placeholder rather than a
working feature, it says so. A guide that describes what is planned as though it
already ran is worse than no guide.

---

## 1. The command line

```
./video-code --file scene.py                 # preview window, live
./video-code --file scene.py --generate out.mp4
./video-code --editor                        # the editing shell
```

| Flag | What it does |
|---|---|
| `--file <path>` | The scene to run. Default `video.py` |
| `--generate <path>` | Render to a file instead of previewing |
| `--width` / `--height` | Output size in pixels. **The only way to set it** — a scene cannot |
| `--framerate` | Output fps. Scenes are authored at 30 fps and resampled |
| `--windowRatio` | Preview window size, as a fraction of the video size |
| `--hwencode` | Encode with `h264_videotoolbox` instead of libx264 — faster, different quality curve |
| `--showstack` | Show the scene's steps while it renders |
| `--showtimeline` | Show the timeline while it renders |
| `--editor` | Open the editing shell |
| `--screenshot <png>` | With `--editor`, write the first painted frame and exit |
| `--visual-test` | Run the visual regression suite |
| `--update-golden` | With `--visual-test`, rewrite the golden images instead of comparing |

`make test-unit` runs the Python suites, `make typecheck` runs pyright,
`make test` runs the visual suite.

---

## 2. The editing shell

`./video-code --editor` opens a window made of one **dock**. Everything in it is
a panel, and every panel can be moved, closed, split off or floated. The chrome
is QML read from disk at run time: saving a `.qml` file rebuilds the window
without restarting.

### The dock

| Gesture | What happens |
|---|---|
| Drag a tab onto another slot's strip | The panel joins that slot |
| Drag a tab near a slot's **edge** | The slot splits in two and the panel takes the new half |
| Drag a tab outside the window | The panel leaves in a window of its own |
| Drag the border between two panes | Both resize |
| Drag a pane's outer edge | The pane resizes even with nothing beside it — the space left over stays empty |
| Close the last tab of a slot | The slot is removed and its space given back |
| Right-click a tab strip | The slot's menu — split, close, display options |

The arrangement is written to `~/Library/Preferences/video-code/dock.json` and
restored on the next launch, floating windows included. Sizes are kept as
fractions of the window, so a dock saved on a monitor still fits a laptop.

### Arrangements

Four shapes to start from, each a whole arrangement with a name, on ⌘1 to ⌘4:

| Name | What it is for |
|---|---|
| **Normal Editing** | The bin, the picture, the timeline — cutting |
| **Vibe Editing** | The picture large, and one column holding the agent, the code, the bin and the timeline as tabs |
| **Video Coding** | The buffer owns the left column; picture and agent on the right |
| **Preview** | The picture and the timeline, nothing else |

Your edits to an arrangement are kept **per arrangement** — coming back to one
gives you your version of it, not the factory one. `Dock display → Reset UI`
puts the current one back to how it ships, and offers to save it first.

**Save display…** names the current arrangement and keeps it beside the four.
A named display reopens exactly as it was named: it is the arrangement you
decided was worth keeping, so an afternoon of dragging does not quietly become
the new version of it. Save over the name again to change it.

### The menu bar

Native macOS menus, not painted by the application.

Left to right: **System** (what you set), **Dock display** (what you arrange),
**Guide** (what you read). The application menu is not part of that order —
macOS keeps it leftmost whatever we do.

- **video-code → Settings…** (⌘,) — code theme, how the bin displays, and where
  the dock is kept, with a reset. macOS puts it here itself, whichever menu it
  was declared in.
- **System → Keyboard Shortcuts** (⌘/) — a drawn keyboard. Hover an action and
  the whole combination lights up, modifiers included; hover a key and it says
  what it does; click a combination and press the new one to rebind it. The
  board reads the same table the code pane obeys, so the two cannot disagree.
- **System → Code theme** — GitHub Dark (the default), Dark 2026, Video-Code.
- **Dock display** — Layout (⌘1…⌘4), Docks (which panels are open), Save
  display…, Load display, Reset UI.
- **Guide → Colors** — what every colour in the interface means, as a hovering
  submenu with swatches.

---

## 3. The panels

### Code — the scene's source, with a language server behind it

This is a full editor, built here rather than hosted: `pyright-langserver` runs
beside the window and answers over LSP.

| What | How |
|---|---|
| **Colour** | Always on. Three palettes; GitHub Dark by default, and Dark 2026 is VS Code's own, token for token |
| **Diagnostics** | Live. A wave under the range, a dot in the gutter, colour by severity; hover it for the message |
| **Hover** | Rest the pointer on a name — what it is, and its type |
| **Completion** | As you type, or ⌃Space. Filtered on every keystroke locally, so the list never lags behind the letters |
| **Signature help** | On `(` and `,` — the whole signature with the argument you are on lit |
| **Go to definition** | F12, or ⌘-click. Opens the file it lands in |
| **Back / forward** | ⌘← and ⌘→, the browser's model, because following a definition is following a link |
| **References** | ⇧F12 — every use, each with its file, its line and the line's text. Click one to go |
| **Rename** | F2 — a field over the word; every use is rewritten, in files that are not open too |
| **Save** | ⌘S writes the buffer to disk |

Every one of those keys is rebindable from System → Keyboard Shortcuts, and the
new binding is kept beside the arrangement.

Line numbers, a band under the caret, no wrapping, and Tab is four spaces
because the buffer is Python.

Two things a language server gives VS Code and not us: **semantic colouring**
and **inlay hints**. Both belong to Pylance, which is Microsoft's and closed;
`basedpyright` provides them and is a drop-in swap the day they matter.

### Preview — the picture, and the transport

Transport buttons, a timecode, the output size and the frame rate.

**The picture itself is a placeholder.** The renderer paints onto a native
surface that Qt Quick cannot composite over; showing real frames here means
moving it onto the underlay path Quick offers. Until then the rectangle is dark
on purpose rather than pretending.

### Timeline — one lane per element

Ordered by when each element starts, so a longer edit reads as a staircase.
A video is **one** element carrying picture and sound together, drawn as one bar
with its waveform inside it — never split across two lanes. The playhead is the
orange line; the zoom slider sits beside the panel's name rather than taking a
strip of its own.

### Media — the bin

Two shapes, chosen in Settings or from the slot's ⋯ menu:

- **Icons** — real thumbnails, made small on purpose: the first frame for a
  video, a quarter-resolution decode for an image. A bin is something you
  recognise before you read it.
- **Details** — a list, for when the column is narrow or you are looking for the
  exact spelling of a filename to type.

The row's background carries the kind's colour — polygon, image, sound, video,
subtitles — rather than a dot beside it. **+ Add media** opens the system's own
file panel.

### Agent — the conversation

A column that shows what the agent ran, what it read and what it found, because
an agent that edits your scene without showing its work is one you cannot check.
**The exchange shown today is a stand-in**: the panel is built, the agent behind
it is not wired yet.

---

## 4. The keys

| Key | What it does |
|---|---|
| F12 / ⌘-click | Go to definition |
| ⇧F12 | Find every use |
| F2 | Rename everywhere |
| ⌘← / ⌘→ | Back / forward through your jumps |
| ⌃Space | Ask for completions |
| ↑ ↓ / ⏎ / ⇥ | Move through and accept a completion |
| esc | Dismiss the list, the uses panel or an overlay |
| ⇥ | Four spaces |
| ⌘S | Save the buffer |
| ⌘1…⌘4 | Switch arrangement |
| ⌘, | Settings |
| ⌘/ | The keyboard list |

---

## 5. Scripting a run

The shell can be driven without a hand on the mouse — which is how every claim
on this page was checked.

| Variable | What it does |
|---|---|
| `VC_SHOT_DELAY` | Milliseconds to wait before `--screenshot` fires |
| `VC_CLICK="x,y,…"` | Synthetic clicks, in order |
| `VC_DRAG="x1,y1,x2,y2"` | A press, some moves and a release |
| `VC_HOVER="x,y"` | The pointer coming to rest — what tooltips and hovers need |
| `VC_TYPE="text"` | Characters, typed |
| `VC_KEYS="F12;Ctrl+Left;Text:name"` | Named keys in order, and literals |
| `VC_PANEL="settings"` \| `"shortcuts"` | Open an overlay reached only from the native menu bar |
| `VC_SCENE_FILE` | The scene the code pane opens |
| `VC_DOCK_FILE` | Use another dock file, so a test never touches yours |

---

## 6. Where things live

| Path | What |
|---|---|
| `scene.py` | The scene the editor opens on |
| `eg.py` | The project's showcase — every feature at once, rendered by CI |
| `videocode/` | The Python API |
| `qml/VideoCode/` | The chrome, read at run time |
| `src/window/Editor.cpp` | The shell: menus, persistence, file access, probes |
| `src/lsp/LanguageServer.cpp` | The LSP client |
| `~/Library/Preferences/video-code/dock.json` | Your arrangement |
| `docs/FEATURES.md` | The Python API, feature by feature |
| `docs/ui/CODE-PANE.md` | Why the editor is ours and not VS Code |
| `docs/ui/BACKLOG.md` | What is decided, and what is not built yet |

---

## 7. Not built yet

Stated plainly, because everything above is:

- **The preview shows no picture** — the renderer has to move to Quick's
  underlay path first.
- **The agent is a stand-in** — the panel exists, nothing answers it.
- **The timeline reads a placeholder scene** — it is not yet fed by the compiled
  buffer, so dragging a clip does not rewrite the code.
- **No undo across the whole application** — the buffer has its own, the dock
  does not.
