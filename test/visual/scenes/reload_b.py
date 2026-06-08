#!/usr/bin/env python3

# Reload-equivalence pair (B side) — see reload_a.py for the matching "before" scene.
#
# Input 0 (Rectangle): byte-identical Create + Apply in both A and B
#   -> exercises the "skip fully-unchanged input" hot-reload path.
# Input 1 (Circle): identical Create args, but a DIFFERENT moveTo timing here
#   -> exercises the "reuse existing object via resetModifications + replay" path.

from videocode import *

Rectangle(width=2, height=2, fillColor=RED_B, strokeColor=WHITE, strokeWidth=0.05) \
    .position(x=-3, y=0) \
    .fadeIn(start=0, duration=0.5)

Circle(radius=1, fillColor=BLUE_B, strokeColor=WHITE, strokeWidth=0.05) \
    .position(x=0, y=2) \
    .moveTo(y=-2, start=0.3, duration=1)
