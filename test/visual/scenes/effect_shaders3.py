#!/usr/bin/env python3

# Visual regression scene — effects batch 3 filter shaders.
# sepia/invert/hueRotate on a colorful gradient (each recolors it in an
# unmistakably different way), posterize on a smooth ramp (flat bands),
# halftone on a white->black ramp (dot size sweeps small -> large).

from videocode import *

Rectangle(width=3.4, height=1.6, fillColor=LinearGradient(BLUE_C, RED_B), strokeColor=TRANSPARENT) \
    .position(-4.2, 2.4).apply(sepia(), duration=1)

Rectangle(width=3.4, height=1.6, fillColor=LinearGradient(BLUE_C, RED_B), strokeColor=TRANSPARENT) \
    .position(0, 2.4).apply(invert(), duration=1)

Rectangle(width=3.4, height=1.6, fillColor=LinearGradient(BLUE_C, RED_B), strokeColor=TRANSPARENT) \
    .position(4.2, 2.4).apply(hueRotate(120), duration=1)

Rectangle(width=3.4, height=1.6, fillColor=LinearGradient(WHITE, BLACK), strokeColor=TRANSPARENT) \
    .position(-2.2, -1.6).apply(posterize(4), duration=1)

Rectangle(width=3.4, height=1.6, fillColor=LinearGradient(WHITE, BLACK), strokeColor=TRANSPARENT) \
    .position(2.2, -1.6).apply(halftone(12), duration=1)
