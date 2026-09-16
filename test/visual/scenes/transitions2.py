#!/usr/bin/env python3

# Visual regression scene — dipToBlack / zoomThrough / slideOver transition
# templates. Three independent pairs, each showing the transition mid-flight
# (frame 8) and settled (frame 15).

from videocode import *
from videocode.template.effect.other.transitions import dipToBlack, slideOver, zoomThrough

# dipToBlack: blue -> red, same spot — a broken brightness ramp would show
# color bleeding through instead of a clean black midpoint.
dbOut = Rectangle(width=2, height=2, fillColor=BLUE_C, strokeColor=TRANSPARENT).position(-5, 0)
dbIn = Rectangle(width=2, height=2, fillColor=RED_B, strokeColor=TRANSPARENT).position(-5, 0).hide()
dipToBlack(dbOut, dbIn, duration=0.5)

# zoomThrough: green zooms up and out, yellow settles down from a zoom-in —
# incoming created (so stacked) BELOW outgoing, so a broken opacity fade
# would hide it entirely instead of a wrong crop/scale showing through.
zIn = Rectangle(width=1.6, height=1.6, fillColor=YELLOW, strokeColor=TRANSPARENT).position(0, 0).hide()
zOut = Rectangle(width=1.6, height=1.6, fillColor=GREEN_A, strokeColor=TRANSPARENT).position(0, 0)
zoomThrough(zOut, zIn, zoom=1.6, duration=0.5)

# slideOver: red-blue gradient stays put, green-yellow gradient slides in on
# top of it (created after, so stacked above) — a broken position ramp would
# either never move or never land.
soOut = Rectangle(width=2, height=2, fillColor=LinearGradient(RED_B, BLUE_C), strokeColor=TRANSPARENT).position(5, 0)
soIn = Rectangle(width=2, height=2, fillColor=LinearGradient(GREEN_A, YELLOW), strokeColor=TRANSPARENT).position(5, 0).hide()
slideOver(soOut, soIn, direction=Direction.RIGHT, distance=2.5, duration=0.5)
