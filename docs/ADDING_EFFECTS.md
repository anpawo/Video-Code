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

- **Param order is ALPHABETICAL by Python attribute name.** `shaderParams()`
  iterates the args as a sorted map — rename an attribute and every GLSL
  `p[i]` index shifts. Document the layout in the GLSL header comment.
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

### 5. Verify

1. `test/effects_test.py`-style assertions on `Context.stack` (no GPU needed).
2. A scene in `test/visual/scenes/` + a case line in `src/test/VisualTest.cpp`.
   Design the scene so a BROKEN shader fails it: pixelate on a circle
   (staircase edges), not on an axis-aligned gradient rect (looks identical
   either way). Fixed seeds for randomized effects.
3. Actually LOOK at the golden PNG before trusting it.
