#!/usr/bin/env python3


from videocode.template.input import *
from videocode.template.misc.chess.chessboard import ChessBoard
from videocode.template.misc.example.marius import *
from videocode import *

p = Plane()

# ─────────────────────────────────────────────────────────────────────────────
# Shadow — wraps a Polygon, then creates an offset, darker, semi-transparent
# copy of its geometry rendered behind it via zIndex.
# ─────────────────────────────────────────────────────────────────────────────

box = Rectangle(width=5, height=2.5, fillColor=BLUE_C, strokeColor=TRANSPARENT)

# Created after `box` — copies its vertices, renders an offset, darker,
# semi-transparent clone behind it via zIndex.
Shadow(box, offset=(0.3, -0.3), color=BLACK | 0.35).apply(blur(5))

# ─────────────────────────────────────────────────────────────────────────────
# Layer order — relative to creation order by default, or controlled
# explicitly:
#   .inFrontOf(other) / .behind(other) — relative to one input
#   .bringToFront()   / .sendToBack()  — relative to everything in the scene
#   .bringForward()   / .sendBackward() — move one layer at a time
# ─────────────────────────────────────────────────────────────────────────────

a = Rectangle(width=3, height=3, fillColor=RED_A, strokeColor=TRANSPARENT)
a.position(-4.5, -2.5)

b = Rectangle(width=3, height=3, fillColor=BLUE_A, strokeColor=TRANSPARENT)
b.position(-3, -2.5)
# created after `a` → in front of it by default

c = Rectangle(width=3, height=3, fillColor=GREEN_A, strokeColor=TRANSPARENT)
c.position(-1.5, -2.5)
# created after `b` → in front of it by default. Order so far (back→front): a, b, c

a.wait(1).bringToFront()  # `a` now in front of everything
b.wait(2).behind(c)  # `b` now behind `c` (but still in front of `a`)
c.wait(3).sendToBack()  # `c` now behind everything
