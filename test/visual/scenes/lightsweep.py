#!/usr/bin/env python3

# Visual regression scene — LightSweep fragment effect (#85).
# A bright band travels across each input's own bounding box over the
# effect's duration. Exercises: default params, a vertical wide band on a
# circle, and per-letter sweep on a Text group (apply broadcasts to letters,
# so each glyph glints over its own bbox).

from videocode import *

Rectangle(width=4, height=2, fillColor=BLUE_C, strokeColor=TRANSPARENT) \
    .position(x=-3, y=1.5) \
    .apply(lightSweep(), start=0, duration=1)

Circle(radius=1.2, fillColor=RED_B, strokeColor=TRANSPARENT) \
    .position(x=3, y=1.5) \
    .apply(lightSweep(width=40, intensity=1, angle=0), start=0, duration=1)

Text("SHINE", fontSize=1, fillColor=GRAY).position(y=-1.5) \
    .apply(lightSweep(width=15, intensity=0.9, angle=30), start=0, duration=1)
