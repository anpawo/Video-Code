#!/usr/bin/env python3

"""
Assertion-based smoke tests for `SurroundingRectangle`
(`videocode/template/input/SurroundingRectangle.py`) — Manim-inspired
`SurroundingRectangle`: a `Rectangle` outline drawn around another `Polygon`'s
bounding box, expanded by `buff`, copying its position/scale/rotation/zIndex.
Run directly: `python3 test/surrounding_rectangle_test.py`
"""

import sys

sys.path.insert(0, ".")

from videocode import Rectangle, Circle, TRANSPARENT, YELLOW, RED
from videocode.template.input._inputs import SurroundingRectangle

failures: list[str] = []


def check(label: str, condition: bool):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


def approx(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) < tol


# ── default: sized to bbox + 2*buff, default styling ────────────────────────
print("SurroundingRectangle(Rectangle): default buff/color")
r = Rectangle(width=2, height=1).position(3, 1)
sr = SurroundingRectangle(r)

check("width == shape width + 2*buff", approx(sr.width, 2 + 2 * 0.25))
check("height == shape height + 2*buff", approx(sr.height, 1 + 2 * 0.25))
check("position matches shape", approx(sr.meta.position.x, 3) and approx(sr.meta.position.y, 1))
check("fillColor is transparent", sr.fillColor == TRANSPARENT)
check("strokeColor defaults to YELLOW", sr.strokeColor == YELLOW)
check("zIndex is one above shape", sr.meta.zIndex == r.meta.zIndex + 1)


# ── custom buff/color, scale/rotation copied ────────────────────────────────
print("SurroundingRectangle(Circle): custom buff/color, scale copied")
c = Circle(radius=1).position(-1, -1).scale(2)
sr2 = SurroundingRectangle(c, buff=0.1, color=RED)

check("width == shape width + 2*buff", approx(sr2.width, c.width + 2 * 0.1))
check("height == shape height + 2*buff", approx(sr2.height, c.height + 2 * 0.1))
check("strokeColor is RED", sr2.strokeColor == RED)
check("scale copied from shape", approx(sr2.meta.scale.x, 2) and approx(sr2.meta.scale.y, 2))


# ── rotation copied ───────────────────────────────────────────────────────
print("SurroundingRectangle: rotation copied")
r3 = Rectangle().rotation(30)
sr3 = SurroundingRectangle(r3)
check("rotation copied from shape", approx(sr3.meta.rotation, 30))


# ── summary ──────────────────────────────────────────────────────────────────
print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All checks passed.")
