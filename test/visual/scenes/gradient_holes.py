#!/usr/bin/env python3

# Visual regression scene — multi-stop linear gradient fills on multi-contour
# glyphs (letters with holes/counters: "O", "B", "A", "g"). Exercises the
# earcut-with-holes clipping added for multi-stop linear fills: previously
# these fills used only the outer ring as boundary, so the gradient bled into
# the holes. The Plane() grid background should be visible through every hole.

from videocode import *
from videocode.template.input._inputs import *

p = Plane()

# "O" — one hole, horizontal 3-stop gradient.
Text("O", fontSize=2, fillColor=LinearGradient(RED, (WHITE, 50), BLUE_B)).position(x=-6.5, y=1)

# "B" — two holes, vertical 3-stop gradient.
Text("B", fontSize=2, fillColor=LinearGradient(GREEN_A, (WHITE, 50), BLUE_B, angle=90)).position(x=-3.9, y=1)

# "A" — one (triangular) hole, diagonal 4-stop gradient.
Text("A", fontSize=2, fillColor=LinearGradient(RED, (rgba(255, 165, 0), 33), (GREEN_A, 66), BLUE_B, angle=45)).position(x=-1.4, y=1)

# "g" — one hole, multi-stop gradient at an off-axis angle.
Text("g", fontSize=2, fillColor=LinearGradient(BLACK, (WHITE, 30), (BLACK, 70), WHITE, angle=120)).position(x=1.2, y=1)
