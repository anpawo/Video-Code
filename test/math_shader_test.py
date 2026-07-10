#!/usr/bin/env python3

"""
Assertion-based tests for the math-shader PAINTS — `mathShader("file.glsl")`
and the bundled presets (silk / fire / starNest).

Paints are FILL STATE and nothing else (see fill_shader_test.py for the
state mechanics): this file pins the preset surface and the taxonomy walls —
a paint is not a FragmentShader, and `.apply()` rejects it outright.

Run directly: `python3 test/math_shader_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.constants import FRAMERATE
from videocode.shader.fragmentShader.silk import SILK_GLSL
from videocode.shader.fragmentShader.fire import FIRE_GLSL
from videocode.shader.fragmentShader.starNest import STAR_NEST_GLSL
from videocode.shader.ishader import FragmentShader, PaintShader

# ── the generic class + presets ──────────────────────────────────────────────
section("mathShader — binding")

m = mathShader("assets/mathshaders/plasma.glsl", speed=2.0, quality=0.5)
check("filepath stored", m.filepath == "assets/mathshaders/plasma.glsl")
check("fps set automatically from FRAMERATE", m.fps == FRAMERATE)
check("speed + quality stored", m.speed == 2.0 and m.quality == 0.5)
check("defaults are speed=1, quality=1",
      mathShader("x.glsl").speed == 1.0 and mathShader("x.glsl").quality == 1.0)

section("presets — mathShader instances pointing at their bundled GLSL")

for name, preset, glsl in (("silk", silk, SILK_GLSL), ("fire", fire, FIRE_GLSL), ("starNest", starNest, STAR_NEST_GLSL)):
    s = preset(speed=3)
    check(f"{name}() is a mathShader on {glsl.split('/')[-1]}",
          isinstance(s, mathShader) and s.filepath == glsl and s.speed == 3)

# ── taxonomy walls ───────────────────────────────────────────────────────────
section("paints are their own shader kind, fills-only")

check("a paint is a PaintShader, NOT a FragmentShader",
      isinstance(silk(), PaintShader) and not isinstance(silk(), FragmentShader))

r = Rectangle(width=2, height=2)
try:
    r.apply(silk(), duration=1)
    check(".apply(paint) raises TypeError (use fillColor=)", False)
except TypeError:
    check(".apply(paint) raises TypeError (use fillColor=)", True)

t = Text("HI", fillColor=fire())
try:
    t.apply(starNest(), duration=1)
    check(".apply(paint) on a Text raises too", False)
except TypeError:
    check(".apply(paint) on a Text raises too", True)

# ── summary ──────────────────────────────────────────────────────────────────
summary()
