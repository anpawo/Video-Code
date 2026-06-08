#!/usr/bin/env python3

# Visual regression scene — static text.
# Exercises the Letter/Polygon glyph pipeline (buildPath + earcut) without animation.

from videocode import *

Text("Hello World!", fontSize=0.6, fillColor=WHITE, strokeColor=BLUE_B, strokeWidth=0.02).position(y=0.5)
Text("video-code", fontSize=0.4, fillColor=RED_B).position(y=-1)
