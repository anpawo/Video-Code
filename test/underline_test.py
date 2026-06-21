#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Underline`
(`videocode/template/input/Underline.py`) — Manim-inspired `Underline`: a
rounded `HorizontalLine` drawn under another `Polygon`'s bounding box,
offset by `buff` below the bottom edge, copying its position/scale/rotation/
zIndex.
Run directly: `python3 test/underline_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Rectangle, TRANSPARENT, WHITE, RED
from videocode.template.input._inputs import Underline

def approx(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) < tol

# ── default: sized to bbox width + 2*buff, sits below the shape ────────────
section("Underline(Rectangle): default buff/color")
r = Rectangle(width=2, height=1).position(3, 1)
u = Underline(r)

check("length == shape width + 2*buff", approx(u.width, 2 + 2 * 0.1))
check("position.x matches shape", approx(u.meta.position.x, 3))
check("position.y sits below shape bottom edge", approx(u.meta.position.y, 1 - (1 / 2 + 0.1 + 0.05 / 2)))
check("fillColor defaults to WHITE", u.fillColor == WHITE)
check("strokeColor is transparent", u.strokeColor == TRANSPARENT)
check("zIndex is one above shape", u.meta.zIndex == r.meta.zIndex + 1)

# ── custom buff/color, scale copied ─────────────────────────────────────────
section("Underline(Rectangle): custom buff/color, scale copied")
r2 = Rectangle(width=2, height=1).position(0, 0).scale(2)
u2 = Underline(r2, buff=0.2, color=RED)

check("fillColor is RED", u2.fillColor == RED)
check("scale copied from shape", approx(u2.meta.scale.x, 2) and approx(u2.meta.scale.y, 2))
check("position.y accounts for scaled height", approx(u2.meta.position.y, -(1 / 2 * 2 + 0.2 + 0.05 / 2)))

# ── rotation: underline follows the shape's rotated edge ────────────────────
section("Underline(Rectangle): rotation copied, offset rotated with shape")
r3 = Rectangle(width=2, height=1).position(0, 0).rotation(90)
u3 = Underline(r3)

check("rotation copied from shape", approx(u3.meta.rotation, 90))
expectedOffset = 1 / 2 + 0.1 + 0.05 / 2
check("offset rotated 90deg (moves along x, not y)", approx(u3.meta.position.x, expectedOffset) and approx(u3.meta.position.y, 0, tol=1e-6))

# ── summary ──────────────────────────────────────────────────────────────────
summary()
