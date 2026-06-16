#!/usr/bin/env python3

# Visual regression scene — stroked text with multi-contour glyphs.
# Letters are filled as outer/holes earcut groups and each contour is stroked
# independently: no bridge edges through counters ('a', 'b', 'o', 'g'), and
# dotted letters ('i', 'j') render the dot as its own outlined contour.

from videocode import *

Text("abodegq ij", fontSize=1.0, fillColor=RED_B, strokeColor=WHITE, strokeWidth=0.05).position(y=1)
Text("ABODEGQ !?", fontSize=1.0, fillColor=BLUE_C, strokeColor=WHITE, strokeWidth=0.05).position(y=-1.5)
