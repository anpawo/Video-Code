#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Shadow`
(`videocode/template/input/Shadow.py`) — an offset, solid-filled copy of
another `Polygon`'s geometry rendered behind it, copying its
position/scale/rotation/zIndex.
Run directly: `python3 test/shadow_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Square, Rectangle, BLACK, TRANSPARENT
from videocode.context import Context
from videocode.template.input._inputs import Shadow

def approx(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) < tol

def stackKeys(i) -> set[str]:
    """What this input actually asks the renderer for on its first frame."""
    return set(Context.stack[i.meta.index].get(0, {}))

# ── scale copied ────────────────────────────────────────────────────────────
section("Shadow(scaled shape)")
s1 = Square(2).scale(2)
sh1 = Shadow(s1)

check("scale copied from shape", approx(sh1.meta.scale.x, 2) and approx(sh1.meta.scale.y, 2))
check("scale reaches the stack", stackKeys(sh1) >= {"Scale"})

# ── rotation copied ─────────────────────────────────────────────────────────
section("Shadow(rotated shape)")
s2 = Square(2).rotation(30)
sh2 = Shadow(s2)

check("rotation copied from shape", approx(sh2.meta.rotation, 30))
check("rotation reaches the stack", stackKeys(sh2) >= {"Rotation"})

# ── both, on a shape moved as well ──────────────────────────────────────────
section("Shadow(scaled + rotated + moved shape)")
s3 = Square(2).scale(x=2, y=3).rotation(45).position(1, 1)
sh3 = Shadow(s3, offset=(0.5, -0.5))

check("scale copied per axis", approx(sh3.meta.scale.x, 2) and approx(sh3.meta.scale.y, 3))
check("rotation copied", approx(sh3.meta.rotation, 45))
# The offset is the light direction, in world units: it must not turn with the
# shape nor grow with its scale.
check("position is shape position + offset", approx(sh3.meta.position.x, 1.5) and approx(sh3.meta.position.y, 0.5))
check("zIndex is one below shape", sh3.meta.zIndex == s3.meta.zIndex - 1)

# ── untransformed shape: unchanged from before scale/rotation were copied ───
# The regression guard for every existing scene: copying an identity scale and
# a zero rotation must not put a no-op on the stack, or every committed golden
# with a Shadow in it asks for different work.
section("Shadow(untransformed shape): nothing new on the stack")
s4 = Rectangle(width=3, height=1.4).position(-4.5, 2.5)
sh4 = Shadow(s4)

check("scale stays identity", approx(sh4.meta.scale.x, 1) and approx(sh4.meta.scale.y, 1))
check("rotation stays zero", approx(sh4.meta.rotation, 0))
check("stack is exactly position + zIndex + blur", stackKeys(sh4) == {"Position", "ZIndex", "Blur"})
check("fill/stroke untouched", sh4.fillColor == (BLACK | 0.5) and sh4.strokeColor == TRANSPARENT)

# ── still a plain Polygon: transformable after creation ─────────────────────
section("Shadow stays transformable after creation")
s5 = Square(2).scale(2)
sh5 = Shadow(s5).scale(3).rotation(15)

check("later scale wins over the copied one", approx(sh5.meta.scale.x, 3) and approx(sh5.meta.scale.y, 3))
check("later rotation applies", approx(sh5.meta.rotation, 15))
check("shape is unaffected by the shadow's own transforms", approx(s5.meta.scale.x, 2) and approx(s5.meta.rotation, 0))

# ── summary ──────────────────────────────────────────────────────────────────
summary()
