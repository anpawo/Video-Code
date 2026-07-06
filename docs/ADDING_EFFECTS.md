# Adding Effects & Fragment Shaders

Two kinds of "effects" exist, with very different costs. Decide first which
one you need:

| | Effect template (pure Python) | Fragment shader (GLSL + C++ + Python) |
|---|---|---|
| What it can do | Animate existing per-frame state: position, scale, rotation, opacity, colors, crop, any `Args` attribute | Change actual pixels: blur, color grading, distortion, masking |
| Files touched | 1 | 4 (+1 the first time you read this) |
| Examples | `highlight`, `popIn`, `shake`, `typewriter`, `wipeIn`, `kenBurns` | `blur`, `vignette`, `pixelate`, `glitch`, `lightSweep` |

---

## A. Effect template (highlight-style)

One file: `videocode/template/effect/other/<name>.py`. The pattern is a
factory returning an `Effect` — a callable that takes an `Input` and yields
per-frame shaders:

```python
def myEffect(*, start: sec = 0, duration: sec = 0.5, easing: easing = Easing.InOut) -> Effect:
    def _apply(input: Input) -> Generator[IShader, Any, None]:
        src = v2(*input.meta.scale)                    # read current state HERE,
        dst = src * 1.5                                #   not in the factory
        for s, i in easing.rangeIdx(src, dst, duration):
            yield _scale(*s).at(start=start + i * SINGLE_FRAME)
    return _apply
```

Usage is `input.apply(myEffect())` — `Input.apply` flattens non-`IShader`
arguments by calling them with the input.

Key facts:

- **Read `input.meta.*` inside `_apply`**, at application time. The factory
  runs before the input reaches its final state.
- **`Group.apply` dispatches the same Effect instance once per member, in
  order.** A closure counter (`index += 1` per call) therefore gives you
  per-member staggering — that's the whole typewriter trick.
- Deterministic offsets (pure sine, no `random`) keep group members rigid
  under broadcast and keep visual-test goldens reproducible (`shake`).
- To persist an end state past the animation, emit a stateful shader at the
  end (`wipeOut` yields `hide()` at `start + duration` — a bare animated
  `crop` evaporates after its last frame).
- Available building blocks: any `VertexShader` (`position`, `scale`,
  `rotation`, `opacity`, `zIndex`, `args(name, value)` for arbitrary
  attributes) and any `FragmentShader` (e.g. per-frame `crop(...)` = wipe).

## B. Fragment shader

Four layers, matched by NAME — `class myshader` (Python) → `"Myshader"`
(stack entry, `upperFirst`) → `X(Myshader)` (C++ factory) → 
`assets/shaders/myshader/frag.glsl` (lowercase folder).

### 1. GLSL — `assets/shaders/<lowername>/frag.glsl`

```glsl
#version 450
layout(location = 0) in vec2 fragUV;                    // absolute frame UV, 0..1
layout(set = 0, binding = 0) uniform sampler2D tex;     // the input's isolated layer
layout(push_constant) uniform PC {
    float texelX;   // 1/frameWidth  (blur passes repurpose these as step direction)
    float texelY;   // 1/frameHeight
    float p[6];     // your params — max 8 floats total
} pc;
layout(location = 0) out vec4 outColor;
void main() { ... }
```

Pipelines are **auto-discovered** — every `assets/shaders/*/frag.glsl` folder
becomes an effect pipeline at startup, in both renderers. No registration
needed for the pipeline itself. GLSL is compiled at runtime (edit + rerun,
no rebuild).

### 2. C++ — `include/shader/ShaderFactory.hpp`

- Constant params → add one line to the `SHADERS(X)` macro.
- Object-relative params (needs the mesh's bounding box) → `BBOX_SHADERS(X)`
  macro. `resolveEffectParams()` (vulkan/EffectResolver.hpp) prepends the
  mesh's screen-space bbox, so your GLSL reads `p[0..3]` = (uMin, vMin,
  uMax, vMax) followed by your args. (`crop`, `vignette`)
- Time-driven → hand-declare a class overriding `paramsAtFrame()` to append
  the 0..1 progress (`LightSweep`, `Glitch` are the references), and add a
  `BIND_SHADERS(...)` line to the factory map.
- Group-union behavior (one continuous effect across a whole `Text`) →
  override `groupParamIndex()`; see `LightSweep` and EffectResolver.hpp.

### 3. Python — `videocode/shader/fragmentShader/<name>.py`

```python
class myshader(FragmentShader):
    def __init__(self, strength: number = 0.5):
        self.strength = strength
```

Export it from `videocode/shader/_shaders.py` (star import).

### 4. The traps (each one cost a debugging session once)

- **Param order is ALPHABETICAL by Python attribute name — and it is easy to
  get this wrong even knowing the rule** (chromaKey's first version assumed
  `tolerance, softness, keyB, keyG, keyR` — its `__init__` assignment order —
  and silently read garbage; the real order is `keyB, keyG, keyR, softness,
  tolerance`). `shaderParams()` iterates the args as a `std::map` after
  C++ conversion (alphabetical), NOT Python's dict insertion order — so
  printing `Context.stack` from Python and eyeballing the key order **does
  not** tell you the true order; a 3-attribute name like `amount`/`slices`/
  `seed` looks insertion-ordered in Python but arrives as `[amount, seed,
  slices]` in GLSL (see `Glitch`). To get it right: alphabetize the
  attribute names in `__init__` BY HAND before writing the GLSL comment, or
  render a test scene where each param has a visually distinct effect and
  confirm the picture matches, not just that the shader "does something."
- **`texelX`/`texelY` are the real texel size only in single-pass effects.**
  Blur's two passes overload them as the step direction — don't copy blur's
  GLSL as a starting point for a non-separable effect.
- **8 floats max** after texelX/Y (`EffectPC.p[8]`). bbox eats 4.
- **The layer texture is the input's isolated rendering** — pixels outside
  the object are transparent, and UV-shifting samples that transparency
  (glitch fringes look right for free). Alpha-weight accordingly.
- **`--visual-test --update-golden` rewrites EVERY golden**, including cases
  that were legitimately failing. After generating goldens for a new scene,
  `git checkout -- test/visual/golden/` then `git add` only the new files.
- **Colors can't ride push constants.** `shaderParams()` only picks numeric
  args — an `rgba` attribute is silently skipped. Flatten colors to float
  attributes in `__init__` (see `duotone.py`: `darkB/darkG/darkR/...`,
  names chosen so the alphabetical order groups the channels).
- **A visual scene must outlive its sampled frames.** The video's length is
  `lastEverAffectedFrame`; if the longest effect ends at frame 27 and the
  test samples frame 29, `readFrame` returns an empty image and the run
  aborts inside `imwrite`. Make one effect's duration cover the last frame.
- **Blend modes are NOT fragment-shader effects.** A `frag.glsl` effect
  post-processes a single input's *isolated* layer (transparent everywhere
  else) — it can never see what's behind the input, so it cannot express
  compositing (multiply/screen/…). Blend modes are pipeline color-blend
  *state* selected per mesh: `Metadata.blendMode → Mesh::blendMode →
  m_pipelines[mode]`, one pipeline variant per mode, bound in the main draw
  loop. The recipe lives once in `include/vulkan/BlendModes.hpp` and both
  renderers build/destroy the `m_pipelines[]` array from it. Overlay is
  intentionally unsupported: it needs the fragment shader to READ the
  destination pixel (subpass input attachment), which fixed-function blend
  factors can't do — a render-pass restructure, not a blend-state tweak.
- **Glow/bloom is the ONE hand-built exception to "an effect samples one
  texture and never composites."** It is NOT a general capability — do not
  assume the effect chain can now read a second texture or destination-blend.
  Glow works by wiring a small fixed sequence directly in the `lower == "glow"`
  branch of both renderers: Passthrough the sharp original into a THIRD scratch
  buffer, run Blur's exact H/V topology in place on ping/pong, Passthrough the
  original back into the target, then one additive pass (`assets/shaders/glow/
  frag.glsl`, which only does `texture * intensity`) drawn with a hand-built
  pipeline that has `blendEnable = VK_TRUE` (ONE, ONE) into a dedicated
  `m_effectPassLoad` render pass (`loadOp = LOAD`, so the additive draw keeps
  the original instead of clearing it). The `glow` folder is deliberately
  SKIPPED by the per-folder auto-discovery loop (which bakes `blendEnable =
  false` + a CLEAR pass) and its combine pipeline is built by
  `createGlowResources()`. If you need another compositing effect, budget for
  the same bespoke plumbing — the generic path won't give it to you.
- **Track mattes / masks are the SECOND hand-built exception** to "one texture,
  no compositing" (after glow) — and unlike every other effect, the first where
  two DIFFERENT inputs interact at draw time. `A.matte(B)` keeps A only where B
  has coverage (a `Video`/gradient clipped to a `Text` silhouette). It is NOT an
  effect-chain feature: matte is a `VertexShader` (`Metadata.matteSource → Mesh::
  matteSourceInputIndex`, a plain input index) resolved entirely in the renderer.
  Mechanism (mirrored in both renderers): the pre-pass phase isolates BOTH the
  consumer (A) and the source (B) into their own `EffectResultSlot`s (the
  isolation gate is extended beyond "has effects" to include matte consumers and
  matte sources; a zero-effect isolated mesh still Passthrough-flushes into its
  slot). A second sub-phase then draws a **2-sampler** combine pass — the first
  2-sampler descriptor layout in the codebase (binding 0 = A's content, binding
  1 = B's matte; `matte/frag.glsl` does `out = vec4(A.rgb, A.a * B.a)`) — into
  ping, and Passthrough-flushes it back over A's own slot. The main draw loop
  then composites A's slot like any effect mesh, and **B is excluded from the
  main draw loop** (standard track-matte convention: the source is consumed only
  as a mask, never drawn). Both the `matte` folder (2-sampler) and its combine
  pipeline are hand-built by `createMatteResources()` and skipped by the generic
  auto-discovery loop, exactly like glow. Do NOT read this as "the effect chain
  can now sample a second texture" — it cannot; matte is bespoke plumbing. The
  matte source must be a single Input (has a `meta.index`); a multi-letter
  `Text` is a Group of Letters, so merge it into one input with `CompoundPolygon`
  first (native Group-matte, unioning member coverage, is a future extension).
- **LUT color grading is the THIRD hand-built exception** (after glow and matte) —
  and a genuinely different kind. `lut("file.cube")` remaps every pixel through a
  standard Adobe/DaVinci `.cube` 3D lookup table. Two things make it its own shape:
  1. **2D-atlas trick instead of a 3D texture.** There is NO `VK_IMAGE_TYPE_3D` /
     `sampler3D` anywhere in the codebase, and LUT does not add any. Instead the
     `.cube`'s N blue-slices are tiled side-by-side into one flat `(N*N) x N` 2D
     image (tile `b` holds the R-G plane for blue slice `b`) — reusing the EXACT
     2D texture path Image/Video use (`uploadTexture`, BGRA `B8G8R8A8_UNORM`). The
     shader (`assets/shaders/lut/frag.glsl`) samples two adjacent blue tiles and
     `mix()`es them (trilinear via 2 bilinear taps; the sampler does R/G interp).
     Parser + atlas builder live in the shared `include/vulkan/LutAtlas.hpp`
     (`parseCubeToAtlas`), same shared-header precedent as EffectResolver.hpp.
  2. **The first effect with a persistent, file-keyed, lazily-cached GPU texture**
     rather than pure per-frame push-constant math. Every prior effect (blur, glow,
     matte) is stateless-per-frame; a LUT needs a texture built ONCE from a file
     and reused every frame/mesh. The `.cube` path is a STRING, so it can't ride the
     numeric `p[]` push-constant array — instead `ActiveEffect` gained a `strParam`
     field (`include/vulkan/Mesh.hpp`), populated in `AInput::getActiveEffectsAtFrame`
     by reading a `"filepath"` arg straight off the effect's JSON (analogous to how
     `Matte` reads `args.at("source")` directly). Each renderer holds a
     `std::unordered_map<filepath, LutResource>` cache, built lazily the first time
     a path is seen in the `lower == "lut"` branch (via `getOrBuildLut`, which calls
     `uploadTexture` so the atlas image lives in `m_textures` and is freed in
     cleanup). Only `intensity` still rides the numeric path (`p[0]`); the renderer
     appends the atlas size as `p[1]` itself. Like glow/matte, the `lut` folder is
     SKIPPED by the generic auto-discovery loop and its 2-sampler pipeline (binding
     0 = content, binding 1 = LUT atlas) + push-constant layout are hand-built by
     `createLutResources()` in both renderers. If a future effect needs to attach a
     file-loaded resource to an effect instance, copy this pattern: a string on
     `ActiveEffect` + a per-renderer file-keyed cache, NOT a push constant.
- **Adjustment layers are the FOURTH hand-built exception** (after glow, matte,
  LUT) — and different in kind again: the first that operates on an arbitrary,
  order-sensitive COMPOSITE of many meshes instead of one/two isolated layers.
  `AdjustmentLayer()` (input/AdjustmentLayer.py) is a full-frame, invisible Input
  whose applied fragment effects grade the flattened composite of every mesh
  drawn BELOW its zIndex — the classic After Effects adjustment layer. It is NOT
  an effect-chain feature: it is a `VertexShader` (`Metadata.isAdjustmentLayer →
  Mesh::isAdjustmentLayer`, a bool marker, no args) resolved entirely in the
  renderers. There is NO new API for attaching effects — the layer uses the same
  `.apply(effect)` every Input has; only the layer marker is new.
  - **Flatten-and-resume mechanism** (mirrored in both renderers): `m_meshes` is
    already z-sorted, so a linear scan in `setMeshes` collects each adjustment
    layer's own position — those positions ARE the chunk boundaries, splitting
    the frame into K+1 contiguous ranges (mirror the matte-source exclusion set:
    an adjustment-layer mesh is added to `m_effectMeshIndices` so it gets a
    result slot, and to `m_adjustmentMeshPositions`, and is NEVER drawn directly).
    In the effect pre-pass loop, an adjustment-layer slot seeds ping via a new
    `recordAdjustmentFlattenPass` (a bounded, offscreen variant of the main draw
    loop — `recordMeshRange` is the shared body) INSTEAD of `recordEffectGeomPass`;
    everything after that (the ping/pong effect chain, the `Passthrough` flush
    into the layer's `EffectResultSlot`) is the completely unchanged effect
    machinery. Chunk 0 flattens `[0, pos_0)` fresh; each later chunk first
    composites the previous layer's graded result (its slot) as a fullscreen quad
    (so grades STACK — a layer grades everything below it, including an earlier
    layer's already-graded result), then draws its own meshes on top. The main
    pass composites only the TOPMOST layer's result quad (which recursively
    contains everything below it) and then draws only the meshes ABOVE it. When
    there are no adjustment layers the flatten path never runs and the main pass
    is byte-identical to before — a true no-op (verify this when touching it).
  - **Renderer asymmetry — call it out, it diverges more here than elsewhere.**
    In the HEADLESS renderer the flatten reuses the existing `m_pipelines[]`
    blend-mode array directly: its main pass and `m_effectPass` are both 1-sample
    `B8G8R8A8_UNORM` (proven by `recordEffectGeomPass` already binding
    `m_pipelines[0]` inside `m_effectPass`). In `VulkanWidget` this does NOT hold:
    its main pass is 4× MSAA + resolve while the flatten target (ping) is
    1-sample, so `m_pipelines[]` (MSAA) cannot bind in `m_effectPass`, and the
    single-mode `m_effectGeomPipeline` can't composite many meshes with their own
    blend modes. The widget therefore builds a PARALLEL 1-sample blend-mode array
    `m_effectBlendPipelines[kBlendModeCount]` (m_pipelines rebuilt at 1 sample
    against `m_effectPass`), used only by its flatten passes. Like the headless
    flatten, the widget flatten is 1-sample (not MSAA) — intermediate chunks
    render at final resolution, the same supersampling tradeoff every blurred/
    matted/LUT'd layer already accepts, extended to a zIndex range.
  - **Known limitation:** matte is finalized in a phase AFTER the effect pre-pass
    loop, so a matte'd mesh that sits below an adjustment layer is flattened with
    its pre-matte content. The AL+matte combination is rare; documented, not fixed.
- **A blend-mode VertexShader resolves its string to an int in Python.** Store
  the resolved `int` on the shader (`self.mode = _MODES[mode]`), never the
  string — the JSON stack and `getMetadataFromArgs` only ever deal with the
  pipeline index. Beware the class-vs-type-alias name collision: a `class
  blendMode` shadows a module-level `type blendMode = Literal[...]`, so name
  the alias distinctly (`blendModeName`) or `from … import blendMode` silently
  gives you the class.

### 5. Verify

1. `test/effects_test.py`-style assertions on `Context.stack` (no GPU needed).
2. A scene in `test/visual/scenes/` + a case line in `src/test/VisualTest.cpp`.
   Design the scene so a BROKEN shader fails it: pixelate on a circle
   (staircase edges), not on an axis-aligned gradient rect (looks identical
   either way). Fixed seeds for randomized effects.
3. Actually LOOK at the golden PNG before trusting it.
