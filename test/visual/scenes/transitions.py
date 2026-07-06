#!/usr/bin/env python3

# Visual regression scene — crossfade / push / wipeBetween transition
# templates. Three independent pairs, each showing the transition mid-flight
# (frame 8) and settled (frame 15).

from videocode import *
from videocode.template.effect.other.transitions import crossfade, push, wipeBetween

# crossfade: blue -> red, same spot
cfOut = Rectangle(width=2, height=2, fillColor=BLUE_C, strokeColor=TRANSPARENT).position(-5, 0)
cfIn = Rectangle(width=2, height=2, fillColor=RED_B, strokeColor=TRANSPARENT).position(-5, 0).opacity(0).hide()
crossfade(cfOut, cfIn, duration=0.5)

# push: green exits left, yellow enters from the right
pOut = Rectangle(width=2, height=2, fillColor=GREEN_A, strokeColor=TRANSPARENT).position(0, 0)
pIn = Rectangle(width=2, height=2, fillColor=YELLOW, strokeColor=TRANSPARENT).position(0, 0).hide()
push(pOut, pIn, direction=Direction.LEFT, distance=2.5, duration=0.5)

# wipeBetween: red-blue gradient wiped away to reveal a green-yellow gradient
wOut = Rectangle(width=2, height=2, fillColor=LinearGradient(RED_B, BLUE_C), strokeColor=TRANSPARENT).position(5, 0)
wIn = Rectangle(width=2, height=2, fillColor=LinearGradient(GREEN_A, YELLOW), strokeColor=TRANSPARENT).position(5, 0).hide()
wipeBetween(wOut, wIn, direction=Direction.LEFT, duration=0.5)
