#!/usr/bin/env python3

# Visual regression scene — lightSweep group semantics.
#
# Top row: three squares whose sweeps share an explicit `group=7` — they are
# swept as ONE area (union of their boxes), so the band lights them one after
# another, left to right.
#
# Bottom row: three squares each with their own lightSweep() instance (fresh
# auto group id) — each sweeps its own box, so they all glint simultaneously.
#
# At the mid-sweep goldens the difference is unambiguous: exactly one top
# square is lit while all three bottom squares are lit at the same spot.

from videocode import *

for x in [-4, 0, 4]:
    Square(2, fillColor=BLUE_C, strokeColor=TRANSPARENT).position(x=x, y=1.6) \
        .apply(lightSweep(width=30, intensity=1, angle=0, group=7), start=0, duration=1)

for x in [-4, 0, 4]:
    Square(2, fillColor=RED_B, strokeColor=TRANSPARENT).position(x=x, y=-1.6) \
        .apply(lightSweep(width=30, intensity=1, angle=0), start=0, duration=1)
