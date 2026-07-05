#!/usr/bin/env python3

# Visual regression scene — effects batch 3 templates (bounceIn, swing,
# tada, stamp). All deterministic. tada runs 1.0s so frame 29 (the last
# sampled golden frame) exists.

from videocode import *
from videocode.template.effect.other.bounceIn import bounceIn
from videocode.template.effect.other.stamp import stamp
from videocode.template.effect.other.swing import swing
from videocode.template.effect.other.tada import tada

Circle(radius=0.6, fillColor=BLUE_C, strokeColor=WHITE, strokeWidth=0.04) \
    .position(-4.5, -1.0).apply(bounceIn(height=2.5, duration=0.9))

Rectangle(width=1.8, height=1.2, fillColor=RED_B, strokeColor=WHITE, cornerRadius=15) \
    .position(-1.5, 0.5).apply(swing(angle=20, duration=0.9))

Rectangle(width=1.5, height=1.5, fillColor=GREEN_A, strokeColor=WHITE, cornerRadius=15) \
    .position(1.5, 0.5).apply(tada(duration=1.0))

Text("STAMP", fontSize=0.55, fillColor=YELLOW) \
    .position(4.5, 0.5).apply(stamp(duration=0.7))
