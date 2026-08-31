# The code pane: what VS Code gives us, and what we would have to build

The question this answers: video-code hosts VS Code in a dock tile today. If we
replaced it with an editor of our own, assembled from open pieces — what is lost
for ever, what is rebuildable, and what did we never need?

Judged against what this pane is *for*: **writing scenes in Python, and
understanding `videocode/` while you write them** — where a function is defined,
what it takes, what it returns, what it does. Everything else is a bonus that has
to earn its place.

## The short answer

- **The intelligence is reproducible.** Definitions, hovers, completion,
  diagnostics, rename, references — all of it comes from a language server over
  LSP, not from VS Code. `pyright` speaks it, standalone and open source.
- **The ecosystem is not.** Extensions are not libraries; they are programs
  written against the `vscode` API and run inside its extension host. Reproducing
  the host is reproducing VS Code — that is Eclipse Theia's entire project.
- **Most of what we would lose, this pane never needed.**

## What is lost, and whether it matters here

| What | What it actually is | Verdict for video-code |
|---|---|---|
| **The extension marketplace** | Any VSIX, installable tomorrow, for a need nobody has predicted | **The only irreversible loss.** Not a feature — an option on the future |
| **Pylance** | Microsoft's closed Python analyser: semantic colouring, inlay hints, faster on large trees | Acceptable. Pyright covers definitions, hovers, completion, diagnostics, rename; inlay hints are the real miss (`fillIn(band=25, reverse=True)` reads better with inferred types) |
| **Copilot** | Inline completion and chat | **Not needed.** The dock already has an agent whose whole job is writing scenes |
| **Remote-SSH, Dev Containers, WSL** | Proprietary remote development | Irrelevant. The scene is a local file |
| **Live Share** | Real-time collaborative editing | Irrelevant today |
| **Notebooks, Testing explorer, Tasks** | Jupyter UI, test tree, task runner | Not needed. The project runs `make`, `--visual-test`, `--generate` |
| **Debug UI** | Breakpoints, call stack, watch, stepping — over DAP | Not needed. A scene is judged by looking at the picture, not by stepping through it. If it ever is, `debugpy` speaks DAP and the protocol is open — the *UI* is the work |
| **Git decorations, blame, diff view** | SCM integration | Not needed in the pane. A terminal is a keystroke away |
| **Search across files** | Regex, globs, include/exclude | **Wanted.** Reading `videocode/` means grepping it. Buildable, or `⇧⌘F` in the real VS Code |
| **Command palette, quick open** | Fuzzy find for files and commands | **Wanted.** A few hundred lines of ordinary work |
| **Settings & keybindings UI** | Schema-validated editors for both | Already ours: `docs/ui/editor.html` has a live keyboard with rebinding by pressing keys |
| **Terminal** | xterm.js integrated | Not needed |

## What we would rebuild, and with what

- **Definitions, hovers, signatures, completion, diagnostics, rename,
  references** → **LSP + pyright**. This is the requirement, and it is a
  protocol, not a product. Any editor can drive it.
- **Syntax colour** → already done (`PythonHighlighter`, a `QSyntaxHighlighter`
  driven from `Theme.code`), or Tree-sitter if it ever needs to be structural.
- **The editor widget** → keep ours (line numbers, current-line band, no
  wrapping, tab as four spaces), or embed **Monaco** (MIT) / **CodeMirror 6** if
  a web view is wanted anyway.
- **Debugging**, the day it matters → **DAP + debugpy**.
- **Quick open, find in files, peek definition** → ordinary application work,
  each a day rather than a week.

## What only OUR editor can do

This is the argument that actually decides it, and it has nothing to do with
features VS Code lacks:

- **The caret and the timeline are the same object.** Click a clip, the call that
  made it lights up; put the caret in a call, the clip highlights. The backlog
  has wanted this from the start; VS Code Web will never expose enough to do it
  cleanly.
- **The playhead in the gutter** — a mark showing where in the scene the current
  frame is.
- **Effects previewed inline**, beside the call that applies them.
- **A gesture rewrites a line** and the editor shows it happening, in the same
  undo history as everything else.

## Measured facts, not impressions

- Hosting VS Code costs, at rest, with the pane visible: **`WebContent` ≈ 9 %
  CPU, `WebKit.GPU` ≈ 5 %**, while video-code itself sits at **0.1–1.2 %**. The
  lag is inside VS Code Web and WebKit, not in our Qt side.
- Three reasons it is heavier than desktop VS Code: the web build runs its
  extension host in a worker and its file system over the server; it is tuned for
  Chromium, and WebKit is its least-optimised target; and a native web view over
  a Metal-rendered window means two compositors on one surface.
- The only structural fix is Chromium instead of WebKit — Qt WebEngine — which
  cannot link statically and would mean rebuilding the whole application against
  a dynamic Qt.

## What hosting VS Code cost us in plumbing

Kept as a record, because none of it was obvious and all of it is load-bearing:

- `code serve-web` opens a Unix socket under the session's temp directory. macOS
  caps a socket path at 104 bytes; a session whose temp directory carries an
  extra component pushes it to ~121, `listen()` fails with EINVAL, and the server
  then holds its HTTP port without ever answering. **Fixed by bootstrapping the
  server into the user's GUI domain** (`launchctl bootstrap gui/<uid>`), whose
  temp directory is the short one.
- Workspace trust is an **application** setting, so no workspace file can turn it
  off — and untrusted workspaces have their settings ignored. **Fixed by seeding
  the user profile**, which for VS Code Web lives in the browser's IndexedDB:
  `vscode-web-db` → `vscode-userdata-store` → `/User/settings.json`, values as
  raw bytes. The side bar's visibility is not a setting but per-workspace state,
  in `vscode-web-state-db-<hash>` → `ItemTable` → `workbench.sideBar.hidden`.
- Opening a file needs `?folder=…&payload=[["openFile","vscode-remote://<host>:<port>/<path>"]]`,
  encoded **exactly once** — going through `QUrlQuery` double-encoded the quotes
  and the workbench silently opened nothing.
- A hidden `WKWebView` does not lay out or paint, so the workbench only started
  booting when the pane was first shown. It is parked **off screen** instead, and
  boots in the background.

## What was decided, and what shipped

**VS Code is gone.** The pane is ours, and pyright answers for it. Removed with
it: `EditorPanel.qml`, `WebPanel.mm/.hpp`, the `code serve-web` launchd service,
the profile seeding, the workspace generation and the WebKit framework link.

What the pane does today, all of it over LSP and all of it verified by a
scripted run rather than by eye:

| Capability | How it is reached | Verified |
|---|---|---|
| Diagnostics | Live, as you type | Squiggle under the range, dot in the gutter, colour by severity, message on hover |
| Hover | Pointer at rest, 400 ms | `(parameter) x: maybe[number]` over `moveBy(x=…)` |
| Completion | Typing, or ⌃Space | `s.mo` → `morphTo`, `moveTo`, `moveBy`, kind letter and colour per row |
| Signature help | `(` and `,` | Whole `Circle(…)` signature, active parameter in orange |
| Go to definition | F12, or ⌘-click | `Square` → `Rectangle.py:46`, scrolled a third down |
| Back / forward | ⌘← / ⌘→ | Returns to the scene with the caret where it was |
| References | ⇧F12 | "4 uses", each with file, line and the line's text; click to jump |
| Rename | F2 | Field over the word; every use rewritten, other files written to disk |
| Colour | Always | `PythonHighlighter`, lexical |

Three things had to be learned the hard way and are worth keeping:

- **A list from the server is array-LIKE, not an array.** `Array.isArray()` is
  false for anything that crossed the QML bridge, which silently turned every
  reply into "not a list" and made go-to-definition do nothing at all. `listed()`
  tests `length` instead.
- **Qt swaps ⌘ and ⌃ on macOS.** ⌘ arrives as `ControlModifier` and ⌃ as
  `MetaModifier`. Reading them the other way round binds nothing, quietly.
- **A second `didOpen` for one URI is a protocol error.** The pane opens a
  document when it loads one and again when the server comes up, so
  `openDocument()` on a known path forwards to `changeDocument()`.

What we knowingly do not have: **semantic colouring and inlay hints**, which are
Pylance's, not pyright's — `basedpyright` provides both and is a drop-in
replacement for the day they matter. And the **extension marketplace**, which is
the one loss that cannot be bought back, and was never what this pane was for.

## Why, in one paragraph

Hosting VS Code worked. It cost 9 % CPU at rest for intelligence that is not VS
Code's to begin with — LSP is a protocol and pyright speaks it standing alone —
and it could never give the one thing this pane exists for: the caret and the
timeline being the same object. Everything above is the floor that makes that
possible.
