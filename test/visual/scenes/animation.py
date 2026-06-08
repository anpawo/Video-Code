#!/usr/bin/env python3

# Visual regression scene — moveTo / fadeIn over time.
# Exercises VertexShader (Position) and FragmentShader (Opacity) timelines.

from videocode import *

Rectangle(width=2, height=2, fillColor=RED_B, strokeColor=WHITE, strokeWidth=0.05) \
    .position(x=-4, y=0) \
    .moveTo(x=4, start=0, duration=1) \
    .fadeIn(start=0, duration=0.5)

Circle(radius=1, fillColor=BLUE_B, strokeColor=WHITE, strokeWidth=0.05) \
    .position(x=0, y=2) \
    .moveTo(y=-2, start=0.2, duration=1)
