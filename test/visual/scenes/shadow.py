#!/usr/bin/env python3

# Visual regression scene — Shadow template (offset, darker, semi-transparent
# copy of a Polygon's geometry, rendered behind it via zIndex).
# Shadow is a plain Polygon snapshot taken at construction time, so the shape
# is positioned first.
# Exercises: default offset/color, custom offset/color, rounded corners,
# Triangle, and an independently-blurred shadow.

from videocode import *
from videocode.template.input._inputs import *

# Default shadow (small offset, default BLACK | 0.5 color)
rect = Rectangle(width=3, height=1.4, fillColor=BLUE_C, strokeColor=TRANSPARENT)
rect.position(-4.5, 2.5)
Shadow(rect)

# Larger offset, custom color
rect2 = Rectangle(width=3, height=1.4, fillColor=GREEN_A, strokeColor=TRANSPARENT)
rect2.position(0, 2.5)
Shadow(rect2, offset=(0.4, -0.4), color=RED | 0.5)

# Rounded corners — shadow should be rounded too
rect3 = Rectangle(width=3, height=1.4, fillColor=BLUE_A, strokeColor=TRANSPARENT, cornerRadius=30)
rect3.position(4.5, 2.5)
Shadow(rect3, offset=(0.3, -0.3))

# Triangle
tri = Triangle(p0=(-1.5, -1), p1=(1.5, -1), p2=(0, 1.5), fillColor=RED_A, strokeColor=TRANSPARENT)
tri.position(-4.5, -1)
Shadow(tri, offset=(0.25, -0.25))

# Shadow is just a Polygon — shaders applied to it don't affect the shape
rect4 = Rectangle(width=2.5, height=1.2, fillColor=GREEN, strokeColor=TRANSPARENT)
rect4.position(0, -1.5)
Shadow(rect4, offset=(0.3, -0.3)).apply(blur(5))
