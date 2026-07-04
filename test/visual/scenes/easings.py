#!/usr/bin/env python3

# Visual regression scene — Easing.Back / Elastic / Bounce rate functions.
# Three balls fall the same distance over the same duration; the sampled
# frames catch them at visibly different heights (overshoot below the target
# for Back/Elastic, staircase landing for Bounce). Frame 29: all settled at
# exactly the same end position.

from videocode import *

Circle(radius=0.4, fillColor=BLUE_C, strokeColor=WHITE, strokeWidth=0.03) \
    .position(-3, 2).moveBy(y=-3, easing=Easing.Back, duration=1)

Circle(radius=0.4, fillColor=RED_B, strokeColor=WHITE, strokeWidth=0.03) \
    .position(0, 2).moveBy(y=-3, easing=Easing.Elastic, duration=1)

Circle(radius=0.4, fillColor=GREEN_A, strokeColor=WHITE, strokeWidth=0.03) \
    .position(3, 2).moveBy(y=-3, easing=Easing.Bounce, duration=1)
