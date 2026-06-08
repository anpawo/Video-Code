#!/usr/bin/env python3

# Visual regression scene — static shapes (no animation).
# Exercises Rectangle / Circle / Triangle Create + basic Position/Align.

from videocode import *

Rectangle(width=3, height=2, fillColor=RED_B, strokeColor=WHITE, strokeWidth=0.05).position(x=-3, y=1)
Circle(radius=1, fillColor=BLUE_B, strokeColor=WHITE, strokeWidth=0.05).position(x=0, y=-1)
Triangle(fillColor=GREEN_A, strokeColor=WHITE, strokeWidth=0.05).position(x=3, y=1)
