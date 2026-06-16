#!/usr/bin/env python3

# Visual regression scene — linear and radial gradient fills and strokes.
# Exercises: LinearGradient (2-stop, angled, multi-stop breakpoints),
# RadialGradient (2-stop, multi-stop), gradient stroke, and gradient on Circle.

from videocode import *

# 2-stop horizontal linear (0° default)
Rectangle(width=3, height=1.4, fillColor=LinearGradient(RED_B, BLUE_B), strokeColor=TRANSPARENT).position(x=-4.5, y=2.5)

# 2-stop vertical linear (90°)
Rectangle(width=3, height=1.4, fillColor=LinearGradient(GREEN_A, BLUE_B, angle=90), strokeColor=TRANSPARENT).position(x=0, y=2.5)

# 2-stop diagonal linear (45°)
Rectangle(width=3, height=1.4, fillColor=LinearGradient(RED_A, GREEN_A, angle=45), strokeColor=TRANSPARENT).position(x=4.5, y=2.5)

# 3-stop linear with a pinned midpoint (30%)
Rectangle(width=3, height=1.4, fillColor=LinearGradient(RED_B, (WHITE, 30), BLUE_B), strokeColor=TRANSPARENT).position(x=-4.5, y=0.5)

# Radial 2-stop on rectangle (red center → blue edge)
Rectangle(width=3, height=1.4, fillColor=RadialGradient(RED_B, BLUE_B), strokeColor=TRANSPARENT).position(x=0, y=0.5)

# Radial 2-stop on circle
Circle(radius=1, fillColor=RadialGradient(WHITE, BLUE_B), strokeColor=TRANSPARENT).position(x=4.5, y=0.5)

# Radial 3-stop on circle (white center → yellow ring → dark edge)
Circle(radius=1, fillColor=RadialGradient(WHITE, (rgba(255, 200, 50), 40), BLUE_B), strokeColor=TRANSPARENT).position(x=-4.5, y=-1.5)

# 5-stop linear rainbow
Rectangle(width=3, height=1.4, fillColor=LinearGradient(RED, (rgba(255, 165, 0), 25), (GREEN_A, 50), (BLUE_B, 75), GRAY), strokeColor=TRANSPARENT).position(x=0, y=-1.5)

# Gradient stroke on a solid rectangle
Rectangle(width=3, height=1.4, fillColor=BLUE_C, strokeColor=LinearGradient(RED_A, GREEN_A, angle=0), strokeWidth=0.12).position(x=4.5, y=-1.5)
