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
| `Video(filepath, cuts, startFrame, endFrame, width, height, cornerRadius, strokeColor, strokeWidth, uvMapping, uvAngle)` | `Video.py` | Video file as a textured `Polygon`. `cuts`/`startFrame`/`endFrame` trim/skip source frames during playback. |
| `Sound(filepath, start, volume, trimStart, trimEnd)` | `Sound.py` | Purely auditory — no visual geometry. `start` = delay (seconds) before it begins playing in the output, `volume` is a 0-1 multiplier, `trimStart`/`trimEnd` cut the source clip. Multiple `Sound`s get mixed together via ffmpeg `amix`. |

`uvMapping` (`Image`/`Video`, default `"stretch"`) controls how the texture is
wrapped onto the shape: `"stretch"` is bbox-normalized UVs (texture stretched
to the bounding box); `"radial"`/`"conic"` are polar UVs around the bbox
center, mirroring `RadialGradient`/`ConicGradient`'s center/angle convention
(`u=radius,v=angle` vs `u=angle,v=radius`). `uvAngle` (degrees) rotates the
angular origin for radial/conic mapping.

**Examples**: `test/visual/scenes/image_shape.py`,
`test/visual/scenes/uv_mapping.py`, `video.py` (scene),
`test/visual/scenes/sound.py` (uses `test/test.wav`).

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
| `grayscale()` | `grayscale.py` | Desaturate |
| `blur(...)` | `blur.py` | Gaussian-style blur |
| `brightness(...)` | `brightness.py` | Brightness adjust |
| `contrast(...)` | `contrast.py` | Contrast adjust |
| `gamma(gamma)` | `gamma.py` | Gamma correction |
| `grain(...)` | `grain.py` | Film-grain noise |
| `crop(...)` | `crop.py` | Crop to a region |
| `lightSweep(...)` | `lightSweep.py` | Animated diagonal light/highlight sweep |

**Examples**: `test/visual/scenes/crop.py`, `lightsweep.py`,
`lightsweep_group.py`.

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

Named colors and directional constants live in `videocode/constants.py`:
`WHITE`, `BLACK`, `TRANSPARENT`, `RED_A/B/C`, `BLUE_B/C`, etc., and
`UP`/`DOWN`/`LEFT`/`RIGHT`/`UR`/`UL`/`DR`/`DL`, `TOP_SIDE`/`BOTTOM_SIDE`/
`LEFT_SIDE`/`RIGHT_SIDE`, `TL`/`TR`/`BL`/`BR`, `ORIGIN`.

**Examples**: `test/visual/scenes/gradient.py`, `gradient_percent.py`,
`gradient_conic.py`, `gradient_holes.py`, `text_gradient.py`.

---

## Effects (`videocode/template/effect/`)

Standalone helper functions/classes that build shader sequences — most are
also exposed as `Input` methods (above) but can be used directly:

| Name | File | What it is |
|---|---|---|
| `moveTo`/`moveBy`, `groupMoveTo`/`groupMoveBy` | `moveTo.py` | Position easing (group variants preserve relative member layout) |
| `scaleTo`/`scaleBy` | `scaleTo.py` | Scale easing |
| `rotateTo`/`rotateBy` | `rotateTo.py` | Rotation easing |
| `alignTo` | `alignTo.py` | Align easing |
| `fadeTo` | `fadeTo.py` | Opacity easing |
| `click(low, up, start, duration, easing)` | `click.py` | Iterable of `scale` shaders producing a "press down/release" pulse — see `ParticlesRay`/`Button` usage |

Easing curves (`videocode/utils/bezier.py`):
- CSS-style cubic-beziers (`CubicBezier`): `Easing.Linear`, `Easing.In`,
  `Easing.Out`, `Easing.InOut`
- Manim-inspired rate functions (`Func`, ported from manim's
  `rate_functions`): `Easing.Smooth`, `Easing.RushInto`, `Easing.RushFrom`,
  `Easing.SlowInto`, `Easing.DoubleSmooth`, `Easing.ExponentialDecay` (0→1),
  and `Easing.ThereAndBack`, `Easing.ThereAndBackWithPause`, `Easing.Wiggle`
  (animate out and back to the start value — `f(0) == f(1) == 0`)
- Custom rate functions: `Func(lambda t: ...)` wraps any `t in [0,1] -> m`
  callable as a `RateFunc`, usable anywhere `easing=` is accepted.

---

## Running / Output (`src/Main.cpp`, `src/compiler/Compiler.cpp`)

| Flag | Effect |
|---|---|
| (none) | Live Qt preview window, hot-reloadable with `Ctrl+R` |
| `--file <path>` | Script to run (default `video.py`) |
| `--generate [out.mp4\|out.png]` | Headless render. `.mp4`/video ext → full encode (with audio muxing if `Sound` inputs exist); image ext → single frame |
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
│   └── effect/            # animation-sequence helper functions
├── color.py               # rgba + gradients
├── constants.py           # world-space constants, named colors, directions
└── serialize.py           # scene -> JSON action stack

src/                        # C++ renderer (Vulkan), Qt window, ffmpeg encoder
test/visual/scenes/         # one small scene per feature, used by --visual-test
video.py                     # living demo script
```
