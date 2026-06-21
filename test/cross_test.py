#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Cross`
(`videocode/template/input/Cross.py`) — Manim-inspired `Cross`: two diagonal
`HorizontalLine`s forming an "X" over another `Polygon`'s bounding box,
expanded by `buff`, copying its position/scale/rotation/zIndex.
Run directly: `python3 test/cross_test.py`
"""

import math
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Rectangle, TRANSPARENT, RED, BLUE
from videocode.template.input._inputs import Cross

def approx(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) < tol

# ── default: two diagonal lines spanning the bbox + 2*buff ──────────────────
section("Cross(Rectangle): default buff/color")
r = Rectangle(width=2, height=1).position(3, 1)
x = Cross(r)

check("two lines", len(x.inputs) == 2)

width = 2 + 2 * 0.1
height = 1 + 2 * 0.1
expectedLength = math.hypot(width, height)
expectedAngle = math.degrees(math.atan2(height, width))

line1, line2 = x.inputs
check("line1 length == diagonal of bbox+2*buff", approx(line1.width, expectedLength))
check("line2 length == diagonal of bbox+2*buff", approx(line2.width, expectedLength))
check("line1 rotated to diagonal angle", approx(line1.meta.rotation, expectedAngle))
check("line2 rotated to mirrored diagonal angle", approx(line2.meta.rotation, -expectedAngle))
check("both lines centered on shape position", approx(line1.meta.position.x, 3) and approx(line1.meta.position.y, 1))
check("both lines centered on shape position", approx(line2.meta.position.x, 3) and approx(line2.meta.position.y, 1))
check("default color is RED", line1.fillColor == RED and line2.fillColor == RED)
check("strokeColor is transparent", line1.strokeColor == TRANSPARENT)
check("zIndex is one above shape", line1.meta.zIndex == r.meta.zIndex + 1)

# ── custom buff/color, scale and rotation copied ─────────────────────────────
section("Cross(Rectangle): custom buff/color, scale+rotation copied")
r2 = Rectangle(width=2, height=1).position(0, 0).scale(2).rotation(45)
x2 = Cross(r2, buff=0.2, color=BLUE)

line1b, line2b = x2.inputs
check("color is BLUE", line1b.fillColor == BLUE)
check("scale copied from shape", approx(line1b.meta.scale.x, 2) and approx(line1b.meta.scale.y, 2))

width2 = 2 + 2 * 0.2
height2 = 1 + 2 * 0.2
expectedAngle2 = math.degrees(math.atan2(height2, width2))
check("rotation includes shape rotation", approx(line1b.meta.rotation, expectedAngle2 + 45))
check("mirrored rotation includes shape rotation", approx(line2b.meta.rotation, -expectedAngle2 + 45))

# ── summary ──────────────────────────────────────────────────────────────────
summary()
