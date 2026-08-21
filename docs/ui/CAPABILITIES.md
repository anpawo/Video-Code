# What this editor is meant to be able to do

Everything a video editor is expected to do, written down once, so the gap
between this one and the ones people already use is a list rather than a
feeling. It is deliberately longer than any roadmap: knowing what is missing is
not the same as promising it.

Grounded in what Premiere Pro, DaVinci Resolve, Final Cut and CapCut actually
ship (see *Sources* at the end), then bent to the one thing that makes this
editor different.

**The rule that governs the whole list.** The scene is Python. The buffer is the
truth, the timeline is a *view* of it, and every gesture in the window is a small
rewrite of the source — never a second document kept in sync. A feature is only
in this list if it can be expressed that way; anything that would need a hidden
project state the code cannot see belongs in *Not this editor* at the end.

**Status.** `●` exists · `◐` partly · `○` nothing yet. The marker is about the
PRODUCT, not the library: `●` means you can do it today, by hand in the buffer or
by gesture. `★` marks what has been named as important.

---

## 1 · Media

- ● Import video, image, sound, SVG, LaTeX as scene inputs
- ● Video trimming at load (`cuts`, `startFrame`, `endFrame`)
- ◐ A bin: list and grid, add by button — no folders, no search, no rename
- ○ Drag a file from the Finder onto the timeline at a chosen time
- ○ Drag from the bin to the timeline (today it writes a line at the caret)
- ○ Folders and collections in the bin, with the agent able to sort into them
- ○ Search and filter the bin by name, kind, duration, resolution
- ○ Thumbnails from the first frame; hover-scrub a clip's thumbnail
- ○ Waveform generated once and cached per file
- ○ Metadata panel: codec, resolution, framerate, duration, colour space, audio channels
- ○ Relink a file that moved; offline media drawn as such rather than crashing
- ○ Proxy media: generate low-res copies, edit against them, render from the originals
- ○ Consolidate and archive: copy everything a scene uses into one folder
- ○ Recently used files, and a project-relative path policy that survives a move

## 2 · The timeline — the grammar of editing

- ● Clips positioned in time, drawn per element, with a ruler and a playhead
- ● Zoom, scrub, snap to a tenth of a second
- ◐ Lanes: one per element, no user-defined tracks yet
- ◐ **Trim**: drag a clip's right edge — it writes `hide(start=…)` under the last
  line that touched the element, counting from the cursor that line left behind.
  The left edge has no handle: where a clip STARTS is where `waitFor`, `flush` and
  `wait` left the clock, which is a statement to move rather than an argument to
  change. A video's `startFrame`/`endFrame` are deliberately NOT this gesture —
  they choose which frames get loaded, and a `Video` cut to thirty frames inside a
  three-second scene still lasts three seconds, so writing them would have moved
  nothing on screen. They stay on the card, beside the rest of the call
- ○ **Ripple trim**: trim and close the gap, everything after moves
- ○ **Roll**: move the cut between two neighbours, total length unchanged
- ○ **Slip**: change what a clip shows without moving it
- ○ **Slide**: move a clip between its neighbours, its own content unchanged
- ○ **Razor / split** at the playhead, on one clip or all lanes
- ○ Insert vs overwrite when dropping onto an occupied lane
- ○ Move a clip in time by dragging it; move it between lanes
- ○ Ripple delete (close the gap) vs lift (leave a hole)
- ○ Multi-selection, rubber-band selection, select all to the left/right
- ○ Copy, cut, paste — including paste attributes only
- ○ Snapping to: clips, the playhead, markers, beats, seconds, frames
- ○ Markers on the timeline and on clips, named and coloured, with comments
- ○ In and out points, and playing only the range between them
- ○ Grouping several clips so they move as one
- ○ Nesting: fold a selection into a compound clip, open it, unfold it
- ○ Track locking, muting, soloing, hiding
- ○ Vertical zoom: taller lanes for waveform work
- ○ Multicam: sync several angles, cut between them live
- ○ Speed: change a clip's rate, with a ramp and a curve — `speedRamps` is in the library, no gesture yet
- ○ Freeze frame, reverse, time-remap keyframes
- ○ J and L cuts: audio leading or trailing the picture
- ○ Detach audio from a video clip; link them again
- ○ Auto-arrange lanes, and a "clean up" that removes empty ones

## 3 · Selecting and inspecting

- ● Click a clip: it leaves its lane and opens in the middle of the window
- ● The element card: kind, duration, source line, its effects on its own axis
- ● Each effect row named by the call that wrote it — `scaleTo`, not `Scale` — and
  marked when it came from a `Group`, where the ✕ takes it off every member
- ● Click an effect row to land on the line that wrote it
- ● Jump from the card to the line of code that created it
- ◐ A group opens into its members; each member opens into its own card
- ○ A properties panel: position, scale, rotation, opacity, anchor, blend, as fields
- ○ Editing a property writes it back to the source, eased or instant
- ○ Multiple selection with shared properties edited at once
- ○ Copy attributes from one element and paste onto others

## 4 · Effects ★

- ● A catalogue of ~30 effects read from the library, never a hand-written list
- ● Entrances, exits, emphasis, filters, each with its real signature
- ● **Set the parameters first, then place it**: the bar you drag is the length it will be
- ● **Drag an effect onto the element** to choose when it starts
- ● Snapping to 0.1 s, ⌘ to drop exactly under the pointer
- ● The card stays open through the whole gesture
- ○ Drop an effect straight onto a timeline clip, without opening the card
- ● Drag an effect's edge on the card to change its duration after the fact
- ● Move an applied effect in time by dragging it — it writes `start=`
- ● Remove an applied effect: the ✕ on its row deletes the call that wrote it —
  a link of a chain loses its link, a statement of its own takes its line
- ○ Reorder effects, and see the order that the render actually uses
- ○ Disable an effect without deleting it
- ○ Favourites, recently used, and a search box in the library
- ○ Effect presets: a configured effect saved under a name, reusable
- ○ Copy an effect from one element to another by dragging
- ○ Apply one effect to a multi-selection in one gesture
- ○ Adjustment layers as a timeline object — the library has `AdjustmentLayer`
- ○ Masks: draw a shape, feather it, invert it, animate it
- ○ Track a mask to a moving subject — `video.track()` exists, no gesture
- ○ An effect's parameters animatable over its own duration (keyframes, see §11)

## 5 · Templates ★

A template here is a Python callable that builds inputs — `CardStack`,
`SplitView`, `Button` and friends already are. What is missing is the way to use
one without typing it.

- ● Composite inputs in the library, parameterised, composable
- ○ A template browser: name, preview, parameters, where it comes from
- ○ **Drag a template onto the timeline** at a chosen time, like an effect
- ○ Its parameters set BEFORE the drop, same rule as effects
- ○ A live preview of the template while dragging, at its real duration
- ○ Resize a placed template by dragging its edge, and decide what stretches:
  the middle stretches, the in and out stay — Premiere calls this responsive time
- ○ Save a selection as a template, named, with the parameters you chose to expose
- ○ A template is a file you can share; a folder of them is a pack
- ○ Nested templates, and a template that takes another as a parameter
- ○ Title templates: lower thirds, credits, callouts, chapter cards
- ○ Transition templates beyond the three the library has
- ○ A starter gallery: what a new scene can begin from

## 6 · Transitions

- ● `crossfade`, `push`, `wipeBetween` between two inputs
- ○ Drop a transition on a cut, not on an element
- ○ Trim a transition's length by dragging it; centre it, or align it to either side
- ○ Default transition with a keyboard shortcut, applied to every selected cut
- ○ Transition presets, and a browser like the effects one
- ○ Handles: know whether the media has frames to spare, and say so when it does not

## 7 · Text and titles

- ● Text as a real input: font, size, weight, italic, per-letter animation
- ● Markdown documents, LaTeX maths, code blocks with syntax colour
- ● Shader fills through the glyphs, strokes, gradients
- ○ Type directly in the preview, where the text will be
- ○ A style panel: face, size, tracking, leading, alignment, fill, stroke, shadow
- ○ Text styles saved and reapplied — change the style, every title follows
- ○ Safe margins and title-safe guides in the preview
- ○ Alignment guides between elements, with snapping
- ○ Text on a path
- ○ Auto-fit: shrink to fit a box, wrap, balance the last line

## 8 · Speech, captions, subtitles

- ● Transcription to a real `.srt`, and `Subtitles` as an input
- ● Beat detection on a sound, for cutting to music
- ○ A caption track you can edit as text, with timings you can drag
- ○ Text-based editing: delete a sentence in the transcript, the picture follows —
  the single biggest workflow change in modern editors
- ○ Word-level karaoke highlighting
- ○ Speaker labels and per-speaker styles
- ○ Import and export `.srt` / `.vtt`, burn in or keep as a track
- ○ Translate captions, keeping the timings

## 9 · Colour, compositing, grading

- ● Blend modes (normal, multiply, screen, add)
- ● Track mattes, adjustment layers, glow, chroma key, LUTs
- ● Shader fills and math shaders as procedural content
- ○ Colour wheels: lift, gamma, gain, offset
- ○ Curves, per channel and by hue/saturation
- ○ Scopes: waveform, vectorscope, histogram, parade
- ○ Colour match between two clips
- ○ Auto white balance and exposure
- ○ A LUT browser with thumbnails, applied by drag
- ○ Per-clip vs per-track vs per-scene grading, and an order you can see
- ○ Colour management: input transforms, working space, output transform

## 10 · Audio

- ● Sound as an input, mixed into the render by ffmpeg
- ◐ A waveform drawn on the timeline — from a hash, not from the file
- ○ Real waveforms, cached
- ○ Volume as a curve on the clip, draggable
- ○ Fades in and out, by dragging the clip's corners
- ○ A mixer: per-track level, pan, mute, solo, meters
- ○ Ducking: music under speech, automatically
- ○ Silence removal, with the fades that keep it from popping
- ○ Noise reduction, EQ, compression, normalisation to a target LUFS
- ○ Audio-only scrubbing, and playback that actually plays sound (there is no audio clock yet)
- ○ Sync audio to video by waveform

## 11 · Animation and keyframes

- ● Every transform is an eased animation: position, scale, rotation, opacity, align
- ● 20+ easing curves, including Manim's rate functions and overshoots
- ● Custom rate functions from any `t → v` callable
- ○ A keyframe editor: values over time, per property, on the card
- ○ Curve editing with handles, and presets for the common shapes
- ○ Keyframes readable BACK from the code, so the graph is the code's view
- ○ Copy and paste keyframes; scale a whole animation in time
- ○ Motion paths drawn in the preview, with handles
- ○ Auto-orient along a path
- ○ Onion skinning while adjusting a motion

## 12 · Motion design

- ● Shapes: rectangle, square, circle, polygon, star, arrow, bezier paths
- ● Groups with rigid-body transforms around an anchor
- ● Composite inputs: cards, buttons, split views, graphs, particles
- ○ A shape tool: draw in the preview, get the line in the code
- ○ Boolean operations on shapes
- ○ Repeaters and arrays
- ○ Parenting one element to another as a gesture
- ○ Physics presets: gravity, spring, inertia

## 13 · Preview and playback

- ● A real Vulkan render of the actual scene, at the pane's size
- ● Transport: play/pause, frame step, home/end, scrub, timecode
- ● Play from the end rewinds and starts again
- ○ Loop a range; play only in/out
- ○ Playback quality: full, half, quarter — and a "why is this slow" readout
- ○ Frame-accurate audio playback (needs the audio clock)
- ○ Safe areas, grids, rulers, guides
- ○ Zoom and pan inside the preview
- ○ Full screen, and a second window on a second display
- ○ Before/after wipe against the unedited source
- ○ Snapshot the current frame to a file

## 14 · Code ↔ timeline — the part no other editor has

- ● The buffer is the scene; ⌘R runs it; saving runs it
- ● The timeline and the preview are built from the executed scene
- ● Clicking a clip finds the line that made it
- ● Adding an effect writes a real line, with the import it needs
- ○ Every gesture writes code — trims, moves, deletes, not only additions
- ○ The line the caret is on highlights its element in the timeline, and back
- ○ One undo stack for both: ⌘Z after a drag undoes the code edit
- ○ Formatting kept stable: a gesture edits one line and leaves the rest alone
- ○ A scene spread over several files, with helpers reloaded properly
- ○ Rename an element everywhere, from the timeline
- ○ Live values: change a number in the code and see it without a full run
- ○ Diff view: what the last gesture changed in the source
- ○ Errors from the run shown on the timeline, not only in the buffer

## 15 · The agent

- ◐ A panel, with a conversation shape — not wired to anything yet
- ○ Edits the scene by writing code, shown as a diff you accept or refuse
- ○ Answers about the library: which effect, which parameter, why it looks wrong
- ○ Reads the render: "the title is unreadable over this shot"
- ○ Does the tedious passes: caption styling, beat alignment, colour matching
- ○ Never renders behind your back, never saves without being asked

## 16 · Render and export

- ● Render to mp4 and gif, at a size given on the command line
- ● Audio mixed in, per-scene background, transparent-friendly compositing
- ○ An export dialog: format, codec, bitrate, size, framerate, range
- ○ Presets per destination: YouTube, Instagram, TikTok, ProRes, lossless
- ○ Export the in/out range, or a marker-to-marker range
- ○ Export a still, a GIF, an audio-only file, a caption file
- ○ Alpha channel export
- ○ Hardware encoding, and a progress that can be cancelled
- ○ Background rendering while you keep editing
- ○ Batch export: several presets from one scene
- ○ Auto-reframe to another aspect ratio, keeping the subject
- ○ Render cache: only what changed is re-rendered

## 17 · Project, history, safety

- ● The dock layout is saved per project, with named displays
- ○ A project file: which scene, which media, which layout, which markers
- ○ Autosave of the buffer, and recovery after a crash
- ○ Undo/redo across code and gestures, with a visible history
- ○ Versions: keep the state before a big change, name it, come back to it
- ○ Open recent, and a start screen that does not assume a file exists
- ○ Collaboration: comments on the timeline, review links, versions

## 18 · The window itself

- ● A dock you rearrange, with named layouts and a default you can update
- ● Panes that show their share of the window, and their size while you drag
- ● The pane that has the keyboard is outlined
- ● Every key rebindable, with a board that shows them
- ○ A command palette: everything by name
- ○ Search across the scene: elements, effects, text, files
- ○ Tooltips that explain rather than repeat the label
- ○ A tutorial layer for the first run
- ○ Keyboard navigation through the whole dock, with visible focus
- ○ Themes beyond the code pane's
- ○ Reduce-motion honoured everywhere (done), and a contrast pass on small text

## 19 · Performance

- ● The scene re-runs in single-digit milliseconds; the preview renders on demand
- ● Hot reload diffs the stack rather than rebuilding it
- ○ Incremental execution: re-run only what the edit touched
- ○ Render cache per element, invalidated by what actually changed
- ○ Proxy previews for heavy sources
- ○ Background thumbnail and waveform generation
- ○ A budget readout: what is slow, and which line is responsible

## 20 · Not this editor

Written down so the list above stays honest.

- No hidden project state that the code cannot express — if a gesture cannot be
  written as Python, the gesture is wrong, not the rule
- No timeline that survives its scene: delete the line, the clip is gone
- No effect the library does not have — the browser is generated from the code
- No cloud account required to open a file
- Not a compositor: node graphs, 3D scenes and particle systems belong to tools
  built for them, and this one calls out to them rather than imitating them

---

## Sources

Grounded in what these ship today, then adapted to a code-first editor:

- [Premiere Pro — AI tools, text-based editing, effect categories (Adobe, 2026)](https://blog.adobe.com/en/publish/2026/01/20/new-ai-powered-video-editing-tools-premiere-major-motion-design-upgrades-after-effects)
- [Premiere Pro — ripple, roll, slip, slide](https://helpx.adobe.com/premiere/desktop/edit-projects/trim-clips/perform-ripple-edits.html)
- [Motion Graphics Templates and responsive time (After Effects / Premiere)](https://helpx.adobe.com/after-effects/using/creating-motion-graphics-templates.html)
- [DaVinci Resolve 20 — keyframe editor on the edit page, silence removal, EQ match](https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_20_New_Features_Guide.pdf)
- [Final Cut Pro — multicam editing](https://support.apple.com/guide/final-cut-pro/edit-multicam-clips-ver23c76d65/mac)
- [CapCut — motion graphics templates](https://www.capcut.com/resource/motion-graphics-templates)
