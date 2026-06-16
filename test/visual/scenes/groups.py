#!/usr/bin/env python3

# Visual regression scene — Group broadcasting transformations to children.
# Exercises Group.position()/Group.moveTo() relaying VertexShaders to each member.

from videocode import *

Group(
    Rectangle(width=1.5, height=1.5, fillColor=RED_B, strokeColor=WHITE, strokeWidth=0.05).position(x=-1),
    Circle(radius=0.75, fillColor=BLUE_B, strokeColor=WHITE, strokeWidth=0.05).position(x=1),
).position(y=1).moveTo(y=-1, start=0, duration=1)
