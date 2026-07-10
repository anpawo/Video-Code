# Video-Code — Feature Map

A tour of what the `videocode` Python API can currently do, with pointers to
the implementing file and a runnable example for each feature. Useful as a
starting point to explore the codebase (e.g. for building the GUI — #117).

General notes:
- **Coordinate system**: world coordinates, **Y is positive upward**, origin
  at screen center. `WORLD_TO_SCREEN_RATIO = 120` maps world units to pixels
  (`videocode/constants.py`). `WORLD_WIDTH`/`WORLD_HEIGHT`/`WORLD_OFFSET_X`/
  `WORLD_OFFSET_Y` give the visible world-space bounds (1920x1080 reference).
- **Everything is an `Input`** (`videocode/input/input.py`) — every shape,
  text, image, video, sound, group, etc. is a subclass and shares the
  transformation/animation API described in [Transformations](#transformations--animation-input-methods).
- **Runnable examples**: `test/visual/scenes/*.py` are small self-contained
  scenes used by the visual-regression suite (`./video-code --visual-test`)
  — each one below maps to the feature(s) it covers. `video.py` is the
  living demo script (`./video-code` to preview, `--generate out.mp4` to
  render).
- Run any scene with `./video-code --file test/visual/scenes/<name>.py` to
  preview it live.

---

## Inputs — Shapes (`videocode/input/shape/`)

All shapes are `Polygon` subclasses (`Polygon.py`) — they share
`fillColor`, `strokeColor`, `strokeWidth`, `cornerRadius` (0-100%, percent of
the shape that becomes rounded), and `sharpCorners` (vertex indices exempt
from rounding).

| Class | File | What it is |
|---|---|---|
| `Polygon(vertices, fillColor, strokeColor, strokeWidth, cornerRadius, sharpCorners, open)` | `Polygon.py` | Base for all shapes — arbitrary vertex list, filled via earcut (handles holes/multi-contour), optional rounded corners |
| `Rectangle(width, height, fillColor, strokeColor, strokeWidth, cornerRadius)` | `Rectangle.py` | |
| `Square(size, ...)` | `Rectangle.py` | `Rectangle` with `width == height` |
| `HorizontalLine(length, ...)` / `VerticalLine(length, ...)` | `Rectangle.py` | Thin rectangles, optionally `rounded` |
| `Circle(radius, fillColor, strokeColor, strokeWidth)` | `Circle.py` | Bezier-approximated circle |
| `Dot(...)` | `Circle.py` | Small filled `Circle` |
| `Triangle(p0, p1, p2, fillColor, strokeColor, strokeWidth, cornerRadius)` | `Triangle.py` | Arbitrary 3-point triangle |
| `EquilateralTriangle` / `RightTriangle` | `Triangle.py` | Convenience constructors |
| `Curve(points, strokeColor, strokeWidth, cornerRadius)` | `Curve.py` | Open polyline/curve (`open=True`, `fillColor=TRANSPARENT`); `.animate()` reveals it point-by-point |
| `FunctionGraph(...)` | `Curve.py` | `Curve` sampled from a math function |

**Examples**: `test/visual/scenes/shapes.py` (basic shapes + corner rounding),
`test/visual/scenes/curve.py` (curve reveal animation), `test/visual/scenes/gradient*.py`
(shapes filled with gradients instead of solid colors).

---

## Inputs — Text & Documents (`videocode/input/shape/text/`)

| Class | File | What it is |
|---|---|---|
| `Letter(char, font, fontSize, ...)` | `Letter.py` | A single glyph outline as a `Polygon` (FreeType + HarfBuzz). Multi-contour glyphs (holes, e.g. "o") handled via earcut-with-holes. |
| `Text(text, fontSize, fontFamily, fillColor, strokeColor, strokeWidth, bold, italic)` | `Text.py` | A line of text — `Group[Offset[Letter]]`, each letter individually positioned |
| `Markdown(filepath, fontSize, fillColor, strokeColor, strokeWidth, x, y, lineSpacing)` | `Markdown.py` | Renders a `.md` file as a stack of `Text` blocks. v1 (block-level only): `#`...`######` headings (size-scaled), `- `/`* ` bullets (rendered "• "), whole-line `**bold**`/`*italic*`, plain paragraphs. See `_MarkdownHelper.py` for `parseMarkdown()`. |
| `Subtitles(filepath, fontSize, fillColor, strokeColor, strokeWidth, y, lineSpacing)` | `Subtitles.py` | Parses a `.srt` file (`_SubtitleHelper.parseSRT()`) into `Text` blocks that `hide()`/`show()` themselves at each cue's start/end time |

**Examples**: `test/visual/scenes/text.py`, `text_stroke.py`, `text_gradient.py`,
`markdown.py` (uses `test/test.md`), `subtitles.py` (uses `test/test.srt`).

---

## Inputs — Media (`videocode/input/media/`)

| Class | File | What it is |
|---|---|---|
| `Image(filepath, width, height, cornerRadius, strokeColor, strokeWidth, uvMapping, uvAngle)` | `Image.py` | Image file as a (optionally rounded/stroked) textured `Polygon`. No `width`/`height` ⇒ natural size. |
| `WebImage(url)` | `Image.py` | Downloads an image (via `curl`) then behaves like `Image` |
| `Video(filepath, cuts, startFrame, endFrame, speedRamps, width, height, cornerRadius, strokeColor, strokeWidth, uvMapping, uvAngle)` | `Video.py` | Video file as a textured `Polygon`. `cuts`/`startFrame`/`endFrame` trim/skip source frames during playback. `speedRamps=[(playbackStart, playbackEnd, rate), ...]` retimes windows of the playback timeline: rate `2.0` = sped up, `0.5` = slow-mo, `0.0` = freeze-frame, `-1.0` = reverse. |
| `Sound(filepath, start, volume, trimStart, trimEnd)` | `Sound.py` | Purely auditory — no visual geometry. `start` = delay (seconds) before it begins playing in the output, `volume` is a 0-1 multiplier, `trimStart`/`trimEnd` cut the source clip. Multiple `Sound`s get mixed together via ffmpeg `amix`. |

`uvMapping` (`Image`/`Video`, default `UVMapping.STRETCH`) controls how the
texture is wrapped onto the shape: `STRETCH` is bbox-normalized UVs (texture
stretched to the bounding box); `RADIAL`/`CONIC` are polar UVs around the bbox
center, mirroring `RadialGradient`/`ConicGradient`'s center/angle convention
(`u=radius,v=angle` vs `u=angle,v=radius`). `uvAngle` (degrees) rotates the
angular origin for radial/conic mapping.

### Video time remapping (`speedRamps`)

```python
video = Video("clip.mp4", speedRamps=[
    (30, 60, 0.0),     # freeze for a second (frames 30-60 of the playback timeline)
    (60, 120, -1.0),   # then play backwards
])
```

How: each `(playbackStart, playbackEnd, rate)` window retimes the post-cut
playback timeline — everything outside the windows plays normally.
**Pros**: composes with `cuts`/`startFrame`/`endFrame`; freeze/reverse/speed
in one param. **Cons**: nearest-frame sampling only (no frame blending for
slow-mo); a `cuts` boundary *inside* a ramp window isn't re-applied by the
ramp's rate math (documented in the docstring).

### Motion tracking (`video.track` + `attachTo`)

```python
video = Video("footage.mp4", width=8, height=4.5)
sticker = Circle(radius=0.3, fillColor=RED_A)
sticker.attachTo(video.track(310, 220))   # x,y = pixel in the SOURCE footage
```

How: `track()` runs OpenCV optical flow over the source frames and returns a
`TrackedPath` (per-frame world positions); `attachTo()` makes any `Input`
follow it. Needs `pip install opencv-python` (lazy — only `.track()` callers).
**Pros**: real tracking, ~sub-pixel accurate on clean footage; the attached
input is a normal `Input` (animate/style it freely). **Cons**: tracking loses
lock on occlusion/fast motion (it then holds the last good position); frame
indices are source-frame space, so it doesn't auto-realign under
`cuts`/`speedRamps`; assumes the `Video` itself doesn't move.

### Beat-sync (`sound.beats`)

```python
sound = Sound("music.wav")
logo = Circle(radius=0.9, fillColor=rgba(255, 150, 40))
for beat in sound.beats():                # timestamps in seconds
    logo.apply(pulse(scale=1.3, start=beat, duration=0.3))
```

How: decodes the audio via ffmpeg and runs spectral-flux onset detection
(numpy only — no librosa); returns second-timestamps that plug into any
effect's `start=`. Tune with `sensitivity` (higher = fewer, stronger onsets)
and `minInterval` (minimum spacing). **Pros**: works on any ffmpeg-decodable
file; no heavy deps. **Cons**: it detects *transients* (drum hits, clicks),
not musical meter — no BPM/downbeat awareness, so legato music without sharp
attacks won't produce beats.

### Auto-captions (`sound.transcribe`)

```python
speech = Sound("interview.mp4")           # Sound accepts video files too
subs = Subtitles(speech.transcribe())     # writes a real .srt, returns its path
```

How: runs faster-whisper (OpenAI Whisper weights, CPU, no PyTorch) and writes
a standard `.srt` the existing `Subtitles` input renders; `model="small"` etc.
for better accuracy, `language="en"` to skip auto-detection. **Pros**:
standard `.srt` output (editable/reusable outside the tool); models cached
after first download. **Cons**: the default `tiny` model trades accuracy for
speed (occasional misheard words); first use downloads ~75MB; CPU-only.

**Examples**: `test/visual/scenes/image_shape.py`,
`test/visual/scenes/uv_mapping.py`, `video.py` (scene),
`test/visual/scenes/sound.py` (uses `test/test.wav`);
`test/track_test.py`, `test/beat_sync_test.py`, `test/transcribe_test.py`
(runnable end-to-end demos with synthetic/checked-in fixtures).

---

## Inputs — SVG (`videocode/input/shape/svg/`)

| Class | File | What it is |
|---|---|---|
| `SVG(filepath, width, height)` | `SVG.py` | Parses an SVG (via `svgelements`) into one `SVGPath` `Polygon` per shape element, each `Offset` to its position within the SVG canvas — `Group[Offset[SVGPath]]` |
| `SVGPath` | `SVGPath.py` | Static `Polygon` holding one precomputed shape's contours |

**Example**: `test/visual/scenes/svg.py`.

---

## Inputs — Math (`videocode/input/shape/tex/`)

| Class | File | What it is |
|---|---|---|
| `MathTex(tex, fillColor, strokeColor, strokeWidth, width, height)` | `MathTex.py` | Renders a LaTeX math expression (e.g. `r"\frac{1}{2} + \int_0^1 x^2 dx"`) as a `Group[Offset[SVGPath]]`, recolored as one unit — `formula.fillColor = RED_A` recolors every glyph |
| `Tex(tex, ...)` | `MathTex.py` | Like `MathTex`, but `tex` is inserted verbatim as the document body instead of being wrapped in `$...$` — for plain text or LaTeX constructs (e.g. `align*`) that shouldn't be in math mode |
| `_TexHelper.texToSVG(tex, mathMode)` | `_TexHelper.py` | Compiles `tex` via `latex` + `dvisvgm --no-fonts` (every glyph becomes an outlined path, no embedded fonts) and caches the result under `.cache/tex/<hash>.svg` |

Requires a LaTeX distribution with `latex` and `dvisvgm` on `PATH` (see
`docs/SETUP_LINUX.md`). Manim-style, Manim isn't a dependency: the SVG output
is loaded through the same `_SVGHelper`/`SVGPath`/`Offset`/`Group` pipeline as
`SVG`.

**Example**: `test/visual/scenes/mathtex.py`.

---

## Composite / Template Inputs (`videocode/template/input/`)

| Class | File | What it is |
|---|---|---|
| `Plane(center)` | `Plane.py` | Background grid (rectangle + horizontal/vertical faint lines) — handy for axes/debugging |
| `Box(size, margin, text, color)` | `Box.py` | Rectangle + centered `Text`, `isHovered` flag for interactivity |
| `Button(width, height, text, color)` / `RedButton` / `GreenButton` / `BlueButton` | `Button.py` | Rounded rectangle + label, `isHovered` flag |
| `Graph(xRange, yRange, xExclude, yExclude, unitSize, fontSize, color, lineThickness)` | `Graph.py` | Cartesian axes with numbered ticks |
| `PositiveGraph`, `GraphPoint` | `Graph.py` | Axes restricted to positive quadrant; a labeled point on a `Graph` |
| `ParticlesRay(size, nbr)` | `Particles.py` | Ring of small lines radiating outward (e.g. for click/sparkle effects) |
| `Shadow(shape, offset, color, blurStrength)` | `Shadow.py` | Copy of another `Polygon`'s geometry, solid-filled, offset, rendered behind via `zIndex` |
| `SurroundingRectangle(shape, buff, color, strokeWidth, cornerRadius)` | `SurroundingRectangle.py` | Rectangle outline around another `Polygon`'s bounding box + `buff`, for highlighting — Manim's `SurroundingRectangle` |
| `Underline(shape, buff, color, strokeWidth)` | `Underline.py` | Rounded line under another `Polygon`'s bounding box, offset by `buff` — Manim's `Underline` |
| `Cross(shape, buff, color, strokeWidth)` | `Cross.py` | Two diagonal lines forming an "X" over another `Polygon`'s bounding box + `buff` — Manim's `Cross` |
| `FocusOn(x, y, color, startRadius, endRadius, duration, easing)` | `FocusOn.py` | Translucent circle that shrinks onto `(x, y)` while fading in — "spotlight converging on a point" — Manim's `FocusOn` |
| `DashedLine(x1, y1, x2, y2, dashLength, dashedRatio, color, strokeWidth)` | `DashedLine.py` | Straight line rendered as evenly-spaced dashes — Manim's `DashedLine`, for annotation/helper lines |
| `Arrow(length, bodyLength, bodyWidth, tipLength, tipHeight, bodyInTip, fillColor, strokeColor, strokeWidth, cornerRadius)` | `Arrow.py` | Single-`Polygon` arrow shape |
| `Cursor()` | `Arrow.py` | Pre-shaped `Arrow` styled as a mouse cursor |

**Examples**: `test/visual/scenes/shadow.py`, `test/visual/scenes/groups.py`,
`test/visual/scenes/chess.py` (chessboard built from these primitives).

---

## Grouping & Composition (`videocode/input/interface/`)

| Class | File | What it is |
|---|---|---|
| `Group(*inputs)` | `Group.py` | Holds multiple `Input`s; `.apply()`/transformation calls broadcast to every member. Subclass it to build composite inputs (see Template Inputs above). |
| `StatefulGroup(*inputs)` | `StatefulGroup.py` | Like `Group`, but snapshots each member's position/scale/rotation/opacity/align at creation and re-applies the group's *delta since creation* to each member — so members that already diverged from each other stay diverged (vs. `Group` collapsing them to the same absolute value) |
| `Offset(input, x, y, r)` | `Offset.py` | Wraps an input with a fixed local-frame offset (rotates with the wrapped input). Used internally by `Text`/`SVG` to place letters/shapes within their parent. |
| `Interface` | `Interface.py` | Common base for `Group`/`Offset` — defines `flush`, `wait`, `waitTo`, `waitFor`, `broadcast` |

**Examples**: `test/visual/scenes/groups.py`, `stateful_group_scale.py`,
`test/visual/scenes/mirror.py`.

---

## Transformations & Animation (`Input` methods, `videocode/input/input.py`)

Every `Input` (shape, text, group, ...) has:

**Instant setters** (apply at a point in time):
- `position(x, y)`, `align(x, y)` (align relative to screen edges, e.g.
  `align(x=RIGHT_SIDE)`), `rotation(degree)`, `scale(factor | x=, y=)`,
  `opacity(o)`, `zIndex(z)`
- Layering: `inFrontOf(other)`, `behind(other)`, `bringToFront()`,
  `sendToBack()`, `bringForward()`, `sendBackward()`, `background()`
- Visibility: `hide(start)`, `show(start)`

**Eased animations** (`start`, `duration`, `easing: RateFunc`):
- `moveTo`/`moveBy`, `scaleTo`/`scaleBy`, `rotateTo`/`rotateBy`,
  `alignTo`, `fadeIn`/`fadeOut`
- Generic: `ease(attr, to, ...)` / `easeTogether(...)` — animate *any*
  `@prop` attribute frame-by-frame (e.g. `Rectangle.ease("width", 5,
  duration=1)`, used for #125's width/height/radius animation)

**Timeline control**:
- Module-level `wait(seconds, stop=None)` — a scheduling gap: nothing new
  happens, and by default the world stays ALIVE (shader fills animate,
  videos play). `stop` pauses selected ambient clocks for the span —
  `Clock.VIDEOS` / `Clock.PAINTS` / `Clock.EFFECTS`, one or a list; paused
  clocks RESUME where they stopped (pause, not skip). Module-level
  `freeze(seconds)` = `wait` stopping all three — a literal freeze-frame.
- `wait(seconds)`, `waitTo(frame)`, `waitFor(otherInput)`, `flush()` —
  sequencing helper, see `Curve.animate()` / `Box`/chains in `chess.py`
  for usage patterns
- `apply(*shaders, start, duration, offset)` — low-level: push raw
  `IShader`s onto the action stack (everything above is sugar over this)

**Mirroring**:
- `mirror(*targets)` / `unmirror(*targets)` — replicate every future shader
  applied to this input onto the target inputs too (cycle-safe). See
  `mirror_transformations_feature` notes / `test/visual/scenes/mirror.py`.

**Callbacks**:
- `addPreCallback`/`addPostCallback` — hook into a shader's
  apply lifecycle

**Examples**: `test/visual/scenes/animation.py`, `layers.py` (zIndex),
`resize.py` (`ease` on width/height/radius), `mirror.py`.

---

## Compositing & Grading

Editor-style compositing — plain `Input` methods and fragment effects
(`docs/ADDING_EFFECTS.md` explains how they work inside the renderer).

### Blend modes — `input.blendMode(BlendMode.…)`

```python
warm = Rectangle(width=3, height=3, fillColor=rgba(200, 120, 80))
cool = Rectangle(width=3, height=3, fillColor=rgba(80, 140, 220)).position(1, 0)
cool.blendMode(BlendMode.MULTIPLY)   # NORMAL / MULTIPLY / SCREEN / ADD
```

How: sets how this input's pixels mix with whatever is drawn behind it
(multiply darkens the overlap, screen lightens, add clips toward white).
**Pros**: per-input, switchable mid-timeline via `offset=`. **Cons**: exact
for opaque pixels but approximate at antialiased edges; `OVERLAY` is
unsupported (needs destination-pixel reads the fixed-function blend can't do).

### Track mattes — `content.matte(source)`

```python
with Context.noRegister():
    letters = Text("HELLO", fontSize=2, fillColor=WHITE).inputs
word = CompoundPolygon(*letters)                       # matte needs ONE input
gradient = Rectangle(width=9, height=2.5, fillColor=LinearGradient(RED, BLUE))
gradient.matte(word)                                   # visible only inside the glyphs
```

How: this input is drawn only where `source` has coverage; `source` itself is
never rendered — it's a pure stencil. Works with any content (video, image,
math shaders). **Pros**: composes with the input's other effects; respects
antialiased edges. **Cons**: the source must be a single `Input` — a
multi-letter `Text` is a Group, so merge it via `CompoundPolygon` first.

### Adjustment layers — `AdjustmentLayer()`

```python
Circle(radius=1, fillColor=RED_A).position(-2, 0).zIndex(1)
Square(side=2, fillColor=BLUE_C).zIndex(1)
AdjustmentLayer().zIndex(5).apply(grayscale(), duration=2)   # grades everything below z=5
Square(side=2, fillColor=YELLOW).position(2, 0).zIndex(10)   # above the layer — untouched
```

How: an invisible full-frame input whose applied fragment effects grade the
flattened composite of everything *below its zIndex*; multiple layers stack
cumulatively. **Pros**: grade many inputs at once without touching them; any
fragment effect works. **Cons**: costs a full-frame flatten pass per layer;
membership is zIndex-based only (no per-input opt-out below the layer).

### Glow — `.apply(glow(radius, intensity))`

```python
Circle(radius=1, fillColor=YELLOW).apply(glow(radius=9, intensity=1.2), duration=2)
```

How: a blurred copy is additively composited back onto the sharp original.
**Pros**: cheap halo, best on bright shapes over the dark background.
**Cons**: the halo can't extend past other inputs drawn on top of it.

### Chroma key — `.apply(chromaKey(color, tolerance, softness))`

```python
footage = Image("greenscreen.png", width=6, height=4)
footage.apply(chromaKey(color=GREEN, tolerance=0.3, softness=0.15), duration=2)
```

How: pixels close to `color` (hue/saturation distance) become transparent.
**Pros**: standard green-screen keying with a soft edge falloff. **Cons**:
cheap/uneven lighting needs `tolerance`/`softness` tuning; strong color spill
on the subject isn't removed.

### LUT color grading — `.apply(lut("file.cube", intensity))`

```python
shot = Image("photo.png", width=8, height=4.5)
shot.apply(lut("assets/luts/warm.cube"), duration=2)
```

How: applies a standard Adobe/DaVinci `.cube` 3D color LUT — the same files
colorists exchange (free packs everywhere). **Pros**: real industry format;
parsed once and cached per file; `intensity` blends toward the original.
**Cons**: none notable — sampled trilinearly via a 2D atlas, so very cheap.

### Shader fills — `fillColor=<shader>` (any shape, and Text)

```python
Rectangle(width=4, height=3, fillColor=silk())          # the shader IS the fill
Text("FIRE", fontSize=2.6, fillColor=fire())            # one pattern across the word

text.fillColor = WHITE                                  # ends the shader at that frame
text.fillColor = starNest()                             # ...or switch shaders mid-video
```

How: a fragment shader is valid anywhere `fillColor` goes — it then PAINTS
the input every frame, as persistent fill state: from assignment until
`fillColor` is reassigned or the video ends. Hiding or fading the input does
NOT end the fill — it's simply not rendered while invisible and is still
there when the input comes back. Signatures use the `paint` alias
(`type paint = rgba | PaintShader`): fragment shaders come in two kinds —
PAINTS generate pixels from position + time (`silk`, `fire`, `starNest`,
any `mathShader`) and can be fills; FILTERS transform existing pixels
(`blur`, `grayscale`, `glow`, `lut`, ...) and belong in `.apply()` — using
one as a fill is a TypeError. On a `Text` this builds the
merged-glyph matte structure internally (one continuous pattern spread
across the word, auto-sized canvas).
**Pros**: reads as what it is (the fill); no durations to manage; switching
segments the timeline exactly where you assign. **Cons**: shader-mode Text
holds a silhouette, not letters — no per-letter animation (native Group
matte, wherewasi, would lift that); a letters-mode Text can't switch to a
shader fill after creation (recreate it instead).

**Examples**: `test/visual/scenes/blend_modes.py`, `matte.py`, `glow.py`,
`lut.py`, `adjustment_layer.py`, `effect_shaders4.py` (chromaKey).

---

## Shaders (`videocode/shader/`)

Shaders are the low-level primitives `apply()`/transformation methods push
onto the action stack; can also be used directly via `.apply(...)`.

**Vertex shaders** (`shader/vertexShader/`) — affect geometry/transform:
`position`, `translate` (relative), `scale`, `rotation`, `align`, `opacity`,
`zIndex`, `hide`, `show`, `args` (raw `Args:<name>` passthrough, e.g. for
animating `points`/`contourSizes`)

**Fragment shaders** (`shader/fragmentShader/`) — post-processing on the
rendered pixels:
| Shader | File | Effect |
|---|---|---|
| `grayscale(strength)` | `grayscale.py` | Desaturate |
| `blur(...)` | `blur.py` | Gaussian-style blur |
| `brightness(...)` / `contrast(...)` / `gamma(gamma)` | | Basic color adjusts |
| `sharpen(...)` | `sharpen.py` | Unsharp-mask sharpening |
| `grain(...)` | `grain.py` | Film-grain noise |
| `crop(...)` | `crop.py` | Crop to a region (object-relative) |
| `lightSweep(...)` | `lightSweep.py` | Animated diagonal light/highlight sweep |
| `vignette(...)` | `vignette.py` | Darkened corners (object-relative) |
| `pixelate(...)` | `pixelate.py` | Mosaic pixelation |
| `glitch(...)` | `glitch.py` | RGB split + random slice offsets (time-driven) |
| `vhs(intensity)` | `vhs.py` | Scanlines + chroma shift + analog noise (time-driven) |
| `duotone(dark, light, contrast)` | `duotone.py` | Two-ink recolor through an S-curve |
| `zoomBlur(...)` | `zoomBlur.py` | Radial "zoom punch" blur |
| `sepia()` / `invert(amount)` / `posterize(...)` / `hueRotate(...)` | | CSS-style color filters |
| `halftone(...)` | `halftone.py` | 45° print-style dot grid |
| `chromaKey(color, tolerance, softness)` | `chromaKey.py` | Green-screen keying — see [Compositing & Grading](#compositing--grading) |
| `glow(radius, intensity)` | `glow.py` | Additive bloom halo — see [Compositing & Grading](#compositing--grading) |
| `lut(filepath, intensity)` | `lut.py` | `.cube` LUT color grade — see [Compositing & Grading](#compositing--grading) |

**Examples**: `test/visual/scenes/crop.py`, `lightsweep.py`,
`lightsweep_group.py`, `effect_shaders*.py`.

### Math shaders — `mathShader("file.glsl")` (procedural content)

```python
# Any fragcoord.xyz / Shadertoy-style fragment shader, loaded by path —
# math shaders are PAINTS: they are the fill, never .apply()'d:
bg = Rectangle(width=16, height=9, fillColor=mathShader("assets/mathshaders/plasma.glsl"))

# Bundled presets — the flagship combo is pattern-through-text:
Text("SILK", fontSize=2, fillColor=silk(speed=1.0, quality=1.0))
Text("FIRE", fontSize=2, fillColor=fire())
```

How: unlike every other fragment shader, a math shader REPLACES the input's
pixels with a generated animated pattern (the input's alpha is kept as
coverage, so it stays inside the shape and composes with `.matte()`). The
GLSL file is compiled at runtime and cached per path — write your own by
copying `assets/mathshaders/plasma.glsl` (the contract is documented in it
and in the `mathShader` docstring); no rebuild, no C++.
**Pros**: the whole Shadertoy/fragcoord universe becomes usable content;
zero-alpha pixels early-out so cost scales with the shape's coverage, and
`quality=` trades raymarch steps for speed. **Cons**: raymarched shaders are
intrinsically heavy at 1080p (measured full-frame: silk ~60ms/frame,
fire ~41ms — fine as partial-coverage content, slow as full-frame preview
backgrounds; plasma-style sine shaders are ~free); a broken GLSL file is
reported once on stderr and the effect is skipped.

| Preset | Source | Cost (full-frame 1080p) |
|---|---|---|
| `silk(speed, quality)` | fragcoord.xyz/s/ae4trrxh port | ~60ms/frame |
| `fire(speed, quality)` | "3D Fire" by @XorDev | ~41ms/frame |
| `starNest(speed, quality)` | "Star Nest" by Pablo Roman Andrioli (MIT) | ~19ms/frame |
| `plasma.glsl` (template) | classic sine plasma | ~free |

**Examples**: `test/visual/scenes/silk.py` (golden-tested at 2 frames),
`test/math_shader_test.py`, `feat.py`.

---

## Color & Gradients (`videocode/color.py`)

| Class | What it is |
|---|---|
| `rgba(r, g, b, a)` | Base color — also constructible from hex string (`rgba("#BBBBBB")`), supports `\|` operator to set alpha (`WHITE \| 0.5`) or override with another color (`BLUE_C \| BLACK`) |
| `LinearGradient(...)` | Multi-stop linear gradient, usable anywhere an `rgba` is (`fillColor=LinearGradient(...)`) |
| `RadialGradient(...)` | Multi-stop radial gradient |
| `ConicGradient(...)` | Multi-stop conic/angular gradient |

Gradients correctly respect holes on multi-contour shapes (e.g. letters with
holes like "o"/"a").

### Background — the `BG` script global

```python
BG = WHITE                          # anywhere in the script — that's it
BG = rgba(18, 32, 84)               # any plain color
BG = LinearGradient(RED_A, BLUE_B)  # gradients work too
```

How: assign a color to the module-level `BG` and stop thinking about it —
resolved after the scene runs, so position in the script doesn't matter. A
plain `rgba` becomes the renderer's clear color (zero draw cost, alpha
ignored); a gradient becomes one static full-frame `Rectangle` layered behind
everything. **Pros**: replaces the manual full-frame-rect + `background()` +
"remember to do it" dance; hot-reload safe. **Cons**: deliberately
color-only — an animated background (e.g. `Plane`) stays explicit
(`Plane().drift()` at the END of the script, so the drift covers the full
duration).

Typed enums also live in `videocode/constants.py` (plus `BlendMode` in
`shader/vertexShader/blendMode.py`): `Direction.LEFT/RIGHT/TOP/BOTTOM` (slides,
wipes, transitions), `Axis.X/Y/BOTH` (shake), `UVMapping.STRETCH/RADIAL/CONIC`
(Image/Video), `BlendMode.NORMAL/MULTIPLY/SCREEN/ADD`.

Named colors and directional constants live in `videocode/constants.py`:
`WHITE`, `BLACK`, `TRANSPARENT`, `RED_A/B/C`, `BLUE_B/C`, etc., and
`UP`/`DOWN`/`LEFT`/`RIGHT`/`UR`/`UL`/`DR`/`DL`, `TOP_SIDE`/`BOTTOM_SIDE`/
`LEFT_SIDE`/`RIGHT_SIDE`, `TL`/`TR`/`BL`/`BR`, `ORIGIN`.

**Examples**: `test/visual/scenes/gradient.py`, `gradient_percent.py`,
`gradient_conic.py`, `gradient_holes.py`, `text_gradient.py`.

---

## Effects (`videocode/template/effect/`)

Standalone generator functions that build shader sequences. Call via `input.apply(*effect(input, ...))`.

### Core (`effect/core/`) — the main animation effects, also wired as `Input` methods

| Name | File | What it is |
|---|---|---|
| `moveTo`/`moveBy`, `groupMoveTo`/`groupMoveBy` | `moveTo.py` | Position easing (group variants preserve relative member layout) |
| `scaleTo`/`scaleBy` | `scaleTo.py` | Scale easing |
| `rotateTo`/`rotateBy` | `rotateTo.py` | Rotation easing |
| `alignTo` | `alignTo.py` | Align easing |
| `fadeTo` | `fadeTo.py` | Opacity easing |
| `click(low, up, start, duration, easing)` | `click.py` | Iterable of `scale` shaders producing a "press down/release" pulse — see `ParticlesRay`/`Button` usage |

### Other (`effect/other/`) — standalone effects, not exposed as Input methods

| Name | File | What it is |
|---|---|---|
| `highlight(input, scaleFactor, color, ...)` | `highlight.py` | Scale pulse + `fillColor` flash via `Easing.ThereAndBack`; `input` must be a `Polygon` |
| `typewriter(...)` | `typewriter.py` | Per-letter staggered reveal on a `Text` |
| `shake(amplitude, frequency, axis=Axis.X, decay)` | `shake.py` | Error/attention shake (deterministic, group-rigid) |
| `popIn(...)` / `bounceIn(...)` / `spinIn(...)` / `blurIn(...)` | | Entrances: overshoot scale, gravity bounce, spin+scale, unblur |
| `slideIn(direction=Direction.LEFT, ...)` / `slideOut(...)` | `slide.py` | Slide + fade entrance/exit |
| `wipeIn(direction, ...)` / `wipeOut(...)` | `wipe.py` | Directional reveal/hide via animated crop |
| `pulse(scale, times, ...)` | `pulse.py` | There-and-back scale pulse (beat-sync's partner) |
| `zoomPunch(...)` / `flash(...)` / `jelly(...)` / `swing(...)` / `tada(...)` / `stamp(...)` | | Emphasis effects (Animate.css-style) |
| `kenBurns(...)` | `kenBurns.py` | Slow pan+zoom for stills |

**Transitions** (`transitions.py`) — plain functions animating TWO inputs at
once (not `.apply()` effects):

```python
crossfade(sceneA, sceneB, duration=0.8)
push(cardA, cardB, direction=Direction.LEFT, distance=4)
wipeBetween(shotA, shotB, direction=Direction.RIGHT)
```

How: call after positioning both inputs at their resting spots; the incoming
input should sit behind the outgoing one (`zIndex`) so nothing flashes early.

Easing curves (`videocode/utils/bezier.py`):
- CSS-style cubic-beziers (`CubicBezier`): `Easing.Linear`, `Easing.In`,
  `Easing.Out`, `Easing.InOut`
- Manim-inspired rate functions (`Func`, ported from manim's
  `rate_functions`): `Easing.Smooth`, `Easing.RushInto`, `Easing.RushFrom`,
  `Easing.SlowInto`, `Easing.DoubleSmooth`, `Easing.ExponentialDecay` (0→1),
  and `Easing.ThereAndBack`, `Easing.ThereAndBackWithPause`, `Easing.Wiggle`
  (animate out and back to the start value — `f(0) == f(1) == 0`)
- Editor-style overshoots: `Easing.Back` (overshoot past 1 then settle),
  `Easing.Elastic` (springy oscillation), `Easing.Bounce` (gravity bounces)
- Custom rate functions: `Func(lambda t: ...)` wraps any `t in [0,1] -> m`
  callable as a `RateFunc`, usable anywhere `easing=` is accepted.

---

## Running / Output (`src/Main.cpp`, `src/compiler/Compiler.cpp`)

| Flag | Effect |
|---|---|
| (none) | Live Qt preview window, hot-reloadable with `Ctrl+R` |
| `--file <path>` | Script to run (default `video.py`) |
| `--generate [out.mp4\|out.mov\|out.webm\|out.gif\|out.png]` | Headless render — the extension picks the format: `.mp4` = h264; `.mov` = ProRes 4444 with real per-pixel **alpha** (transparent background); `.webm` = VP9 with alpha; `.gif` = 2-pass palette (no alpha/audio); image ext → single frame. Audio (`Sound` inputs) muxed where the container allows. |
| `--width` / `--height` | Output resolution (default 1920x1080) |
| `--framerate` | Output fps — scenes are authored at 30fps and resampled |
| `--hwencode` | Hardware H.264 encode (videotoolbox, macOS) |
| `--showstack` / `--showtimeline` | Debug printing during generation |
| `--visual-test [--update-golden]` | Run/refresh the golden-frame visual-regression suite (`src/test/VisualTest.cpp`, `test/visual/golden/`) |

`videocode/serialize.py` — `execScene()` (used by the C++ embed) and
`serializeScene()` (for CLI/inspection) turn a scene script into the JSON
action-stack representation the renderer consumes.

---

## Where things live (quick map)

```
videocode/
├── input/
│   ├── input.py          # Input base class — transform/animation API
│   ├── interface/         # Group, StatefulGroup, Offset, Interface
│   ├── shape/             # Polygon + all shape subclasses, text/, svg/
│   └── media/              # Image, Video, Sound
├── shader/
│   ├── vertexShader/      # geometry/transform shaders
│   └── fragmentShader/    # pixel post-processing shaders
├── template/
│   ├── input/             # composite inputs (Plane, Box, Button, Graph, ...)
│   └── effect/            # animation-sequence helper functions (core/, other/)
├── color.py               # rgba + gradients
├── constants.py           # world-space constants, named colors, directions
└── serialize.py           # scene -> JSON action stack

src/                        # C++ renderer (Vulkan), Qt window, ffmpeg encoder
test/visual/scenes/         # one small scene per feature, used by --visual-test
video.py                     # living demo script
```
