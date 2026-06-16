#!/usr/bin/env python3

# Visual regression scene — per-object Crop (pixel masking relative to each
# input's own bounding box, like CSS clip-path: inset()).
# Exercises: left/right crop, top+bottom crop, a centered "window" crop, a
# bottom-half circle, a cropped letter, and crop combined with rotation
# (crops to the rotated screen-space bounding box — an AABB-based
# simplification, not a rotated crop rect).

from videocode import *

# Crop 30% off the left side
Rectangle(width=3, height=1.6, fillColor=RED_B, strokeColor=TRANSPARENT).position(x=-4.5, y=2.2).apply(crop(left=30))

# Crop 30% off the right side
Rectangle(width=3, height=1.6, fillColor=BLUE_C, strokeColor=TRANSPARENT).position(x=0, y=2.2).apply(crop(right=30))

# Crop 25% off the top and bottom (horizontal slice)
Rectangle(width=3, height=1.6, fillColor=GREEN_A, strokeColor=TRANSPARENT).position(x=4.5, y=2.2).apply(crop(top=25, bottom=25))

# Circle cropped to its bottom half
Circle(radius=1.2, fillColor=BLUE_A, strokeColor=TRANSPARENT).position(x=-4.5, y=-0.5).apply(crop(top=50))

# Triangle cropped to a centered window (20% off each side)
Triangle(fillColor=RED_A, strokeColor=TRANSPARENT).position(x=0, y=-0.5).apply(crop(left=20, right=20, top=20, bottom=20))

# Text cropped on the right (cuts off part of the word)
Text("Bonjour", fontSize=0.8, fillColor=WHITE).position(x=4.5, y=-0.5).apply(crop(right=50))

# Rotated rectangle cropped — crops to its rotated screen-space bounding box
Rectangle(width=2.5, height=1.5, fillColor=GREEN, strokeColor=TRANSPARENT).position(x=-4.5, y=-3).apply(rotation(30)).apply(crop(left=25))
