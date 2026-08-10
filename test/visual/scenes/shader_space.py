#!/usr/bin/env python3

# Visual regression scene — `Space`, the math-shader anchoring modes.
#
# Checked at TWO frames (0 and 29) because three of the four modes are only
# distinguishable over time: every square below is scaling, and what differs
# is what the pattern does while it grows.
#
#   SHAPE  (top left)  the pattern scales WITH the square — the same pattern
#                      point stays at the same spot inside it. A regression to
#                      per-frame re-anchoring shows up as the pattern boiling.
#   FRAME  (top right) the square is a moving window onto a frame-wide
#                      pattern: the pixels under it never change.
#   ANCHOR (bottom)    frozen at the fill's assignment frame, so growing
#                      UNCOVERS the pattern instead of resampling it.
#
# The clock is stopped (speed=0) throughout: any difference between frame 0 and
# frame 29 is geometry, never time. plasma is the cheap dense pattern — a
# starfield is mostly black, which hides exactly the drift being tested.

from videocode import *

BG = rgba(8, 10, 24)

GLSL = "assets/mathshaders/plasma.glsl"

for x, y, space in (
    (-5.2, 2.2, Space.SHAPE),
    (0, 2.2, Space.FRAME),
    (5.2, 2.2, Space.ANCHOR),
):
    sq = Square(side=3, fillColor=mathShader(GLSL, speed=0, space=space)).position(x, y).scale(0.55)
    sq.scaleTo(factor=1.35, duration=1.0)

# GROUP, on the one thing it exists for: separate inputs sharing ONE paint
# instance, so the two squares show two halves of a single pattern instead of
# a centred copy each. Under SHAPE these two would be pixel-identical.
shared = mathShader(GLSL, speed=0, space=Space.GROUP)
Square(side=2.4, fillColor=shared).position(-1.6, -2.4)
Square(side=2.4, fillColor=shared).position(1.6, -2.4)
