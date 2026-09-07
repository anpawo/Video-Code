#!/usr/bin/env python3

"""F17 — Row, Column and Grid: the gap is measured between drawn edges."""

from videocode import *
from videocode.template.input.Layout import Column, Grid, Row

Row(
    Square(side=0.6, fillColor=BLUE_C, strokeColor=TRANSPARENT),
    Square(side=1.2, fillColor=GREEN_A, strokeColor=TRANSPARENT),
    Square(side=0.9, fillColor=rgba(240, 180, 90), strokeColor=TRANSPARENT),
    gap=0.3,
).position(-3.5, 2)

Column(
    Rectangle(width=1.6, height=0.4, fillColor=BLUE_C, strokeColor=TRANSPARENT),
    Rectangle(width=1.6, height=0.9, fillColor=GREEN_A, strokeColor=TRANSPARENT),
    gap=0.3,
).position(3.5, 2)

Grid(
    *[Square(side=0.7, fillColor=rgba(120, 150, 220), strokeColor=TRANSPARENT) for _ in range(6)],
    cols=3, rowGap=0.3, colGap=0.3,
).position(0, -1.5)

wait(1)
