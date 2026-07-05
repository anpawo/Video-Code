#!/usr/bin/env python3

# Visual regression scene — chromaKey fragment shader.
# A green rectangle (the "screen") sits behind a keyed foreground rectangle
# that is mostly the key color with a colored patch — after keying, the
# green should vanish (transparent, background dot shows through) and only
# the non-green patch remains opaque.

from videocode import *

Circle(radius=1.2, fillColor=RED_B, strokeColor=TRANSPARENT).position(-3, 0)

# CompoundPolygon isn't needed — two overlapping Rectangles, back one solid
# color to prove transparency, front one chroma-keyed.
Rectangle(width=2.6, height=2.6, fillColor=GREEN, strokeColor=TRANSPARENT) \
    .position(-3, 0).apply(chromaKey(color=GREEN, tolerance=0.35, softness=0.1), duration=1)

Rectangle(width=2.6, height=2.6, fillColor=RED_B, strokeColor=TRANSPARENT) \
    .position(3, 0).apply(chromaKey(color=GREEN, tolerance=0.35, softness=0.1), duration=1)
