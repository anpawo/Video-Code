#!/usr/bin/env python3


from constants import *
from videocode.input.shape.Line import Line
from videocode.input.text.Text import Text


class numberLine:
    def __init__(self) -> None:
        c = rgba(128, 128, 128, 196)

        th = 0.05
        l = 0.25
        s = 0.75
        fontTh = 2

        horizontal = Line(length=WORLD_WIDTH, color=c, thickness=th)
        vertical = Line(length=WORLD_HEIGHT, color=c, thickness=th).rotate(90)

        # Horizontal
        for i in range(1, WORLD_WIDTH // 2):
            Line(length=l, color=c, thickness=th).position(x=i).rotate(90)
            Text(str(i), fontSize=s, fontThickness=fontTh).position(x=i, y=0.35)
        for i in range(1, WORLD_WIDTH // 2):
            Line(length=l, color=c, thickness=th).position(x=-i).rotate(90)
