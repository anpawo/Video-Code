#!/usr/bin/env python3

# Visual regression scene — dipToBlack / zoomThrough / slideOver transition
# templates. Three independent pairs, each showing the transition mid-flight
# (frame 8) and settled (frame 15).

from videocode import *
from videocode.template.effect.other.transitions import dipToBlack

# dipToBlack: blue -> red, same spot — a broken brightness ramp would show
# color bleeding through instead of a clean black midpoint.
dbOut = Rectangle(width=2, height=2, fillColor=BLUE_C, strokeColor=TRANSPARENT).position(-5, 0)
dbIn = Rectangle(width=2, height=2, fillColor=RED_B, strokeColor=TRANSPARENT).position(-5, 0).hide()
dipToBlack(dbOut, dbIn, duration=0.5)
