#!/usr/bin/env python3

from __future__ import annotations

from videocode.constants import FRAMERATE
from videocode.shader.ishader import PaintShader
from videocode.ty import point, unumber


__all__ = ["mathShader"]


class mathShader(PaintShader):
    """
    Generic procedural "math shader" — runs an arbitrary fragment-GLSL file
    (fragcoord.xyz-style ports) as a content source. The file is compiled
    once on first use and cached per path by both renderers; `silk()` is a
    bundled preset of this, and `assets/mathshaders/plasma.glsl` is the
    cheap template to copy for your own. A math shader is a PAINT — it is
    used as fill state, not applied as an effect:

        rect = Rectangle(width=4, height=3, fillColor=mathShader("my/shader.glsl"))
        title = Text("HI", fontSize=2, fillColor=mathShader("assets/mathshaders/plasma.glsl"))

    A math shader REPLACES the input's pixels with its generated pattern,
    keeping only the input's alpha (shape coverage, antialiasing included) —
    so it stays inside the host shape and composes with `.matte()`.

    The GLSL contract (see `assets/mathshaders/plasma.glsl` for a complete
    minimal example — copy its declarations verbatim):

    - `layout(location = 0) in vec2 fragUV;` — absolute frame UV, 0..1.
    - `layout(set = 0, binding = 0) uniform sampler2D tex;` — the input's
      isolated layer; sample its `.a` first and early-out on 0 (the effect
      pass is a fullscreen quad — skipping uncovered pixels is what keeps
      cost proportional to the shape instead of the frame).
    - push constants: `texelX`/`texelY` (1/frame size) then `float p[]`,
      which every math shader reads the same way — a FIXED head, then its own
      args, then the clock:

        p[0..3]  the host shape's screen-space box: uMin, vMin, uMax, vMax,
                 in absolute frame UV (prepended by resolveEffectParams)
        p[4..5]  the origin inside that box — percent of it, or pixels from
                 its top-left when p[6] is 1
        p[6]     the origin's unit: 0 = percent, 1 = pixels
        p[7..]   the shader's OWN numeric args, in ALPHABETICAL order — the
                 trap documented in docs/ADDING_EFFECTS.md. A stock preset has
                 fps, quality, speed, so p[7], p[8], p[9]
        last     elapsed frames since the effect started, appended per-frame
                 by MathShader::paramsAtFrame

      The head is fixed because a math shader draws around a point: it must
      read that point at the same index whatever its own args are called.
      A stock preset therefore derives seconds as `T = p[10] / p[7] * p[9]`,
      and one carrying extra args finds its clock further along — declare
      `float p[N]` with N = 7 + your arg count + 1, and see evileye.glsl for a
      worked example. EffectPC holds 24 floats; anything past that is dropped.
    - `layout(location = 0) out vec4 outColor;` — write
      `vec4(yourColor, coverage)`.

    - `filepath`: the fragment-GLSL file, relative to the working directory
      or absolute. A missing/broken file is reported on stderr once and the
      effect is skipped — the input shows unmodified while you fix it.
    - `speed`: time multiplier (0 freezes the pattern on its first frame).
    - `quality`: 0..1 cost/fidelity knob — the binding always sends it, but
      it only does something if the GLSL uses it (silk scales its raymarch
      step count; trivial shaders like plasma ignore it).
    - `scale`: zoom of the generated pattern around `origin` — >1 magnifies it,
      <1 shrinks everything so more of it fits inside the shape.
    - `origin`: where the pattern is centred INSIDE ITS HOST, as a percentage
      of the host's bounding box — `(50, 50)`, the default, is its middle, so
      a shaped host shows the middle of the pattern instead of whatever
      happened to fall on that part of the frame. Pass `pixels=True` to give
      it in pixels from the box's top-left instead.
    - `pixels`: read `origin` as pixels rather than percent.
    """

    # Presets that need their own uniforms subclass this (see evilEye) — they
    # are all MathShader to the C++ factory.
    cppName = "MathShader"

    def __init__(
        self,
        filepath: str,
        speed: unumber = 1.0,
        quality: unumber = 1.0,
        scale: unumber = 1.0,
        origin: point = (50, 50),
        pixels: bool = False,
    ):
        self.filepath = filepath
        # Hoisted out of the alphabetical p[] by IFragmentShader::pushMathParams
        # — these three always land on p[4], p[5], p[6].
        self.originX = origin[0]
        self.originY = origin[1]
        self.originUnit = 1.0 if pixels else 0.0
        self.fps = FRAMERATE
        self.speed = speed
        self.quality = quality
        self.scale = scale
