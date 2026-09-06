#!/usr/bin/env python3

"""
Assertion-based tests for `nextTo` (D1): the gap is edge to edge in the four
directions, the cross axis is centred on the other input, a scaled shape is
measured as drawn (X6), a corner applies the gap on both axes, a group is
measured by its content, and `follow=True` refuses until S1.
Every expected number is worked out by hand in the comment beside it.
Run directly: `python3 test/next_to_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Rectangle, Square, Circle, Group, UP, DOWN, LEFT, RIGHT, UR


def approx(a: float, b: float, eps: float = 1e-6) -> bool:
    return abs(a - b) <= eps


def at(inp, x: float, y: float) -> bool:
    return approx(inp.meta.position.x or 0, x) and approx(inp.meta.position.y or 0, y)


# ── Four directions, gap edge to edge ───────────────────────────────────────
# a is 4 x 2 at (1, 1); b is a unit square. RIGHT: a's right edge is at 3,
# gap 0.5, b's centre 0.5 further right → 4. Cross axis stays at a's y = 1.
section("nextTo — gap is edge to edge, cross axis centred on the other")
a = Rectangle(width=4, height=2).position(1, 1)
check("RIGHT lands at (4, 1)", at(Square(side=1).nextTo(a, RIGHT, gap=0.5), 4, 1))
check("LEFT lands at (-2, 1)", at(Square(side=1).nextTo(a, LEFT, gap=0.5), -2, 1))
# a's top edge is at 2; gap 0.5; b's centre 0.5 above → 3.
check("UP lands at (1, 3)", at(Square(side=1).nextTo(a, UP, gap=0.5), 1, 3))
check("DOWN lands at (1, -1)", at(Square(side=1).nextTo(a, DOWN, gap=0.5), 1, -1))
check("default gap is 0.25 → RIGHT at 3.75", at(Square(side=1).nextTo(a), 3.75, 1))
check("nextTo returns the input, for chaining", isinstance(Square(side=1).nextTo(a, UP), Square))

# ── A scaled shape is measured as drawn ─────────────────────────────────────
# Square(2).scale(2) draws 4 wide (X6). Beside a unit square at the origin,
# RIGHT, gap 0: 0.5 + 2 = 2.5, not 0.5 + 1.
section("nextTo — the drawn size, not the geometry")
big = Square(side=2).scale(2)
big.nextTo(Square(side=1), RIGHT, gap=0)
check("a doubled square sits 2.5 to the right, its drawn half-width", at(big, 2.5, 0))
# And the other way round: the OTHER is scaled. Unit square beside it: 2 + 0.5.
check("beside a doubled square, a unit square sits at 2.5", at(Square(side=1).nextTo(Square(side=2).scale(2), RIGHT, gap=0), 2.5, 0))

# ── A corner applies the gap on both axes ───────────────────────────────────
# Circle radius 1 at (0, 0); unit square UR, gap 0.2: (1 + 0.5 + 0.2) on each axis.
section("nextTo — a corner")
check("UR lands at (1.7, 1.7)", at(Square(side=1).nextTo(Circle(radius=1), UR, gap=0.2), 1.7, 1.7))

# ── A group is measured by its content ──────────────────────────────────────
# Two unit squares at x = -2 and x = 2: the group spans -2.5 .. 2.5, centred
# on 0. A unit square RIGHT of it, gap 0.5: 2.5 + 0.5 + 0.5 = 3.5.
section("nextTo — beside a group, and a group beside something")
g = Group(Square(side=1).position(-2, 0), Square(side=1).position(2, 0))
check("right of a 5-wide group: 3.5", at(Square(side=1).nextTo(g, RIGHT, gap=0.5), 3.5, 0))
# The group itself moved beside a unit square at (0, 0), LEFT, gap 0.5: its
# content is 5 wide, so its centre goes to -(0.5 + 0.5 + 2.5) = -3.5. A group's
# `meta.position` is a displacement from its pivot (0 here), so -3.5 exactly.
g2 = Group(Square(side=1).position(-2, 0), Square(side=1).position(2, 0))
g2.nextTo(Square(side=1), LEFT, gap=0.5)
check("a 5-wide group left of a unit square: -3.5", at(g2, -3.5, 0))

# ── follow=True is S1's, and says so ────────────────────────────────────────
section("nextTo — follow refuses, naming S1")
try:
    Square(side=1).nextTo(a, UP, follow=True)
    check("follow=True raises", False)
except NotImplementedError as e:
    check("follow=True raises, and names S1", "S1" in str(e))

summary()
