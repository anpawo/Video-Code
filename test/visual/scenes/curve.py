#!/usr/bin/env python3

# Visual regression scene — open polygons (Curve as Polygon with open=True).
# Exercises: plain polyline (sharp corners, no fill, no closing segment),
# rounded interior corners on an open path (endpoints stay sharp), a smooth
# densely-sampled function curve, and Curve.animate() draw-on.

import math

from videocode import *

# Zigzag polyline, sharp corners
Curve([(-6, 1.5), (-5, 3), (-4, 1.5), (-3, 3)], strokeColor=RED_B, strokeWidth=0.06)

# Same zigzag with rounded interior corners (endpoints stay sharp)
Curve([(-1.5, 1.5), (-0.5, 3), (0.5, 1.5), (1.5, 3)], strokeColor=BLUE_B, strokeWidth=0.06, cornerRadius=60)

# Smooth sine curve through many points
Curve([(2.5 + i * 0.04, 1.8 + math.sin(i * 0.25) * 0.8) for i in range(81)], strokeColor=GREEN_A, strokeWidth=0.05)

# Animated draw-on (12 frames)
Curve([(-3 + i * 0.06, -2.5 + math.cos(i * 0.2) * 1.2) for i in range(101)], strokeColor=WHITE, strokeWidth=0.05).animate(0.4)
