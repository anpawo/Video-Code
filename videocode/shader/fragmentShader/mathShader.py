#!/usr/bin/env python3

from __future__ import annotations

from videocode.constants import FRAMERATE
from videocode.shader.ishader import PaintShader
from videocode.ty import unumber


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
    - push constants: `texelX`/`texelY` (1/frame size) then `float p[6]`
      with `p[0]`=fps, `p[1]`=quality, `p[2]`=speed (ALPHABETICAL arg order
      — the trap documented in docs/ADDING_EFFECTS.md) and `p[3]`=elapsed
      frames, appended per-frame by the C++ side (`MathShader` in
      ShaderFactory.hpp). Derive seconds as `T = p[3] / p[0] * p[2]`.
    - `layout(location = 0) out vec4 outColor;` — write
      `vec4(yourColor, coverage)`.

    - `filepath`: the fragment-GLSL file, relative to the working directory
      or absolute. A missing/broken file is reported on stderr once and the
      effect is skipped — the input shows unmodified while you fix it.
    - `speed`: time multiplier (0 freezes the pattern on its first frame).
    - `quality`: 0..1 cost/fidelity knob — the binding always sends it, but
      it only does something if the GLSL uses it (silk scales its raymarch
      step count; trivial shaders like plasma ignore it).
    """

    def __init__(self, filepath: str, speed: unumber = 1.0, quality: unumber = 1.0):
        self.filepath = filepath
        self.fps = FRAMERATE
        self.speed = speed
        self.quality = quality
