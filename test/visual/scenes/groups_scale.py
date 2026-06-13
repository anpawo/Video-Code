#!/usr/bin/env python3

# Visual regression scene — Group broadcasting scale deltas to children.
# Exercises Group.scaleBy() relaying relative scale changes while preserving
# each member's own scale (rect at 1.5x, circle at 0.5x stay 1.0 apart).

from videocode import *

Group(
    Rectangle(width=1, height=1, fillColor=RED_B, strokeColor=WHITE, strokeWidth=0.05).position(x=-1).scale(1.5),
    Circle(radius=0.5, fillColor=BLUE_B, strokeColor=WHITE, strokeWidth=0.05).position(x=1).scale(0.5),
).scaleBy(x=0.5, y=0.5, start=0, duration=1)
