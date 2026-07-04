#!/usr/bin/env python3

# Visual regression scene — vignette / pixelate / glitch fragment shaders.
# vignette: object-centered darkening (bbox-resolved like Crop/LightSweep).
# pixelate: screen-pixel mosaic cells.
# glitch: time-driven slice offsets + RGB split — fixed seed so the slice
# pattern is deterministic for the golden comparison.

from videocode import *

Rectangle(width=3.5, height=2.2, fillColor=LinearGradient(BLUE_C, RED_B), strokeColor=TRANSPARENT) \
    .position(x=-3, y=1.5) \
    .apply(vignette(intensity=0.8, radius=30, smoothness=50), duration=1)

# A circle, not a rect: pixelation must show as staircase blocks on the
# curved silhouette — an axis-aligned gradient rect would look identical
# with a broken (passthrough) pixelate.
Circle(radius=1.2, fillColor=LinearGradient(GREEN_A, BLUE_C), strokeColor=TRANSPARENT) \
    .position(x=3, y=1.5) \
    .apply(pixelate(24), duration=1)

Text("GLITCH", fontSize=0.9, fillColor=WHITE).position(y=-1.5) \
    .apply(glitch(amount=1.2, slices=14, seed=7), duration=1)
