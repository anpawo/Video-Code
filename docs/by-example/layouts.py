#!/usr/bin/env python3

"""
Row, Column and Grid — laying things out by their real size.

Render it:      ./video-code --file docs/by-example/layouts.py --generate layouts.mp4
Look at it:     ./video-code --file docs/by-example/layouts.py --generate layouts.png

Every gap below is measured EDGE TO EDGE, in world units — one unit is 120 px,
so the 1080p world is 16 by 9. `gap=0.5` is 60 px between two borders, whatever
the shapes are. That is the whole difference with `XAlign`, which spaces centres
by a fixed pitch and therefore leaves unequal borders as soon as two members are
not the same width.
"""

from videocode import *
from videocode.template.input.Layout import Column, Grid, Row
from videocode.template.input.Shadow import Shadow

TITLE = 0.42
LABEL = 0.22


# ── 1. A row of things that are NOT the same size ────────────────────────────
# Wide rectangle, small circle, tall square: the borders are 0.4 apart in both
# gaps. Under XAlign the centres would be evenly spaced and the borders would
# not be.
row = Row(
    Rectangle(width=2.4, height=1, fillColor=BLUE_C, strokeColor=WHITE),
    Circle(radius=0.35, fillColor=RED_B, strokeColor=WHITE),
    Rectangle(width=0.7, height=1.6, fillColor=GREEN_A, strokeColor=WHITE),
    gap=0.4,
).position(0, 2.4)

Text("Row — 0.4 between borders, not between centres", fontSize=LABEL).position(0, 1.2)


# ── 2. The cross axis: start, center, end ────────────────────────────────────
# Same three heights, three different answers to "line up on what".
def sample(align: Align, x: float) -> Row:
    return Row(
        Rectangle(width=0.5, height=1.2, fillColor=BLUE_C, strokeColor=TRANSPARENT),
        Rectangle(width=0.5, height=0.6, fillColor=BLUE_C, strokeColor=TRANSPARENT),
        Rectangle(width=0.5, height=0.9, fillColor=BLUE_C, strokeColor=TRANSPARENT),
        gap=0.15,
        align=align,
    ).position(x, -0.4)


for alignment, x in ((Align.START, -5.2), (Align.CENTER, -2.6), (Align.END, 0.0)):
    sample(alignment, x)
    Text(alignment.name.lower(), fontSize=LABEL).position(x, -1.6)


# ── 3. A Row inside a Column ─────────────────────────────────────────────────
# A group is placed by its CONTENT, so nesting lands where the arithmetic says
# rather than on the inner group's origin.
Column(
    Text("nested", fontSize=TITLE),
    Row(*(Circle(radius=0.22, fillColor=RED_B, strokeColor=TRANSPARENT) for _ in range(4)), gap=0.2),
    gap=0.25,
).position(4.2, -0.6)


# ── 4. Grid ──────────────────────────────────────────────────────────────────
# Seven squares in three columns: the last row is short, and stays flush.
Grid(
    *(Square(side=0.5, cornerRadius=20, fillColor=GREEN_A, strokeColor=TRANSPARENT) for _ in range(7)),
    cols=3,
    gap=0.18,
).position(-4.6, -3.0)

Text("Grid(cols=3)", fontSize=LABEL).position(-4.6, -4.2)


# ── 5. A shadow now follows the shape it belongs to ──────────────────────────
# `Shadow` copies its shape's scale and rotation, so a turned, enlarged square
# no longer casts a small upright one.
badge = Square(side=0.8, cornerRadius=15, fillColor=RED_B, strokeColor=WHITE).scale(1.4).rotation(20).position(1.4, -3.0)
Shadow(badge, offset=(0.12, -0.12))

Text("Shadow keeps scale + rotation", fontSize=LABEL).position(1.4, -4.2)


# ── 6. Part of a line can be bold, italic or another colour ──────────────────
# One Text, three styles, and the tags are styling rather than letters on screen.
MarkupText(
    'a <b>subtitle</b> can be <i>styled</i> <font color="#FF6A00">in place</font>',
    fontSize=LABEL,
).position(4.6, -3.6)


# ── 7. An animation of no length lands its value ─────────────────────────────
# `duration=0` used to be silence for everything but moving. It arrives now.
flash = Circle(radius=0.3, fillColor=BLUE_C, strokeColor=WHITE).position(6.4, 2.4)
flash.fill(RED_B, duration=0)

Text("fill(duration=0)", fontSize=LABEL).position(6.4, 1.7)

wait(1)
