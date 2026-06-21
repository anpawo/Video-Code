#!/usr/bin/env python3

"""
Assertion-based smoke tests for `DashedLine`
(`videocode/template/input/DashedLine.py`) — Manim-inspired `DashedLine`: a
straight line from `(x1, y1)` to `(x2, y2)` rendered as a series of evenly
-spaced `HorizontalLine` dashes.
Run directly: `python3 test/dashed_line_test.py`
"""

import math
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import TRANSPARENT, RED, WHITE
from videocode.template.input._inputs import DashedLine

def approx(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) < tol

# ── horizontal line: dashes evenly spaced, aligned ───────────────────────────
section("DashedLine(0,0 -> 3,0): horizontal, default styling")
d = DashedLine(0, 0, 3, 0)

expectedN = round(3 / 0.16)
check("dash count matches length/dashLength", len(d.inputs) == expectedN)

for dash in d.inputs:
    check("each dash horizontal (rotation 0)", approx(dash.meta.rotation, 0))
    check("each dash length == dashLength*dashedRatio", approx(dash.width, 0.16 * 0.5))
    check("default fillColor is WHITE", dash.fillColor == WHITE)
    check("strokeColor is transparent", dash.strokeColor == TRANSPARENT)

check("first dash near start", d.inputs[0].meta.position.x < d.inputs[-1].meta.position.x)
check("dashes span from x1 to x2", 0 < d.inputs[0].meta.position.x < 3 and 0 < d.inputs[-1].meta.position.x < 3)

# ── diagonal line: dashes rotated to the line's angle ───────────────────────
section("DashedLine(0,0 -> 1,1): diagonal, custom color/dashedRatio")
d2 = DashedLine(0, 0, 1, 1, color=RED, dashedRatio=80)

expectedAngle = math.degrees(math.atan2(1, 1))
for dash in d2.inputs:
    check("each dash rotated to line angle", approx(dash.meta.rotation, expectedAngle))
    check("custom color is RED", dash.fillColor == RED)
    check("custom dashedRatio applied", approx(dash.width, 0.16 * 0.8))

# ── summary ──────────────────────────────────────────────────────────────────
summary()
