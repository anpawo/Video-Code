#!/usr/bin/env python3

# Visual regression scene — the `BG` script global (scene clear color).
#
# BG = a deep blue, with two shapes on top. A broken pipeline shows the
# historical dark-gray (0.2) background instead of blue — unmistakable at
# every uncovered pixel. The shapes prove drawing still composites normally
# over the custom clear.

from videocode import *

BG = rgba(18, 32, 84)

Circle(radius=1.2, fillColor=rgba(255, 190, 60), strokeColor=TRANSPARENT).position(-2.5, 0)
Rectangle(width=2.6, height=2.6, fillColor=WHITE, strokeColor=TRANSPARENT, cornerRadius=20).position(2.5, 0)
