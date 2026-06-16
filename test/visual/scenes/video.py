#!/usr/bin/env python3

# Visual regression scene — mirrors the current video.py showcase scene.
# Exercises: Plane background, Shadow's default auto-blur + zIndex-behind
# behavior (per-mesh effect pass fix), and sendToBack layering.

from videocode import *
from videocode.template.input._inputs import *

p = Plane()

r = Rectangle(width=4)
s = Shadow(r)
s = Square(3).sendToBack()
