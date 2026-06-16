#!/usr/bin/env python3

# Visual regression scene — animating width/height/radius (#125 Phase 2).
#
# `Input.ease(attr, to, duration=...)` is generic over any attribute. Since
# `width`/`height`/`radius` are `@prop(onSet=Polygon.updatePoints)`, each
# eased step rebuilds `points` and pushes a fresh Args:points shader — a
# smooth, frame-by-frame geometry animation (mesh rebuilt every frame), with
# no dedicated "resizeTo" template needed.

from videocode import *
from videocode.template.input._inputs import *

p = Plane()

r = Rectangle(width=2, height=2, fillColor=GREEN | BLACK).position(x=-4, y=-1)
r.ease("width", 6, duration=1)

c = Circle(radius=0.5, fillColor=BLUE_C | BLACK).position(x=3, y=0)
c.ease("radius", 2, duration=1)
