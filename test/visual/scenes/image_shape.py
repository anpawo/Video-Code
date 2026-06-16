#!/usr/bin/env python3

# Visual regression scene — Image as a polygon shape.
# Exercises: Image with explicit width/height + cornerRadius + stroke (new
# BezierPath-backed textured fill), a natural-size Image with cornerRadius
# but no width/height (auto-probed natural-size shape), and a plain
# natural-size Image (legacy 4-vertex quad path, for backward-compat
# comparison).

from videocode import *

Image("wb.png", width=3, height=3, cornerRadius=30, strokeColor=WHITE, strokeWidth=0.1).position(x=-2.5, y=0)
Image("wb.png").scale(2).position(x=2.5, y=0)
Image("wb.png", cornerRadius=30, strokeColor=WHITE, strokeWidth=0.1).position(x=0, y=2.5)
