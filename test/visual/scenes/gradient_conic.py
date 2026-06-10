#!/usr/bin/env python3

# Visual regression scene — ConicGradient fills.
# Exercises: 2-stop conic with a hard seam (default angle=0), seamless
# multi-stop "color wheel" (first stop color == last stop color), an angled
# seam (angle=90), and a rectangle to exercise the boundary "corner extras".

from videocode import *

# 2-stop conic on a circle: hard seam at angle=0 (right) where BLUE meets RED
Circle(radius=1.2, fillColor=ConicGradient(RED, BLUE), strokeColor=TRANSPARENT).position(x=-4.5, y=2.5)

# Seamless multi-stop "color wheel" (first == last == RED, no visible seam)
Circle(radius=1.2, fillColor=ConicGradient(RED, (rgba(255, 200, 50), 33), GREEN, (BLUE_B, 66), RED), strokeColor=TRANSPARENT).position(x=0, y=2.5)

# Conic with angle=90 (seam rotated to point up)
Circle(radius=1.2, fillColor=ConicGradient(WHITE, (rgba(255, 200, 50), 50), BLACK, angle=90), strokeColor=TRANSPARENT).position(x=4.5, y=2.5)

# Conic on a rectangle — exercises corner-extra splicing (no black corner gaps)
Rectangle(width=3, height=1.4, fillColor=ConicGradient(RED, GREEN, BLUE, WHITE), strokeColor=TRANSPARENT).position(x=-4.5, y=-1)

# Conic on a rectangle, seamless wrap (matching first/last stop colors)
Rectangle(width=3, height=1.4, fillColor=ConicGradient(BLUE_B, WHITE, BLUE_B), strokeColor=TRANSPARENT).position(x=0, y=-1)

# Conic on a rectangle at angle=45
Rectangle(width=3, height=1.4, fillColor=ConicGradient(RED, BLUE, angle=45), strokeColor=TRANSPARENT).position(x=4.5, y=-1)
