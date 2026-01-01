#!/usr/bin/env python3


from constants import *
from videocode.input.shape.Line import line
from videocode.input.text.Text import text


class numberLine:
    def __init__(self) -> None:
        c = rgba(128, 128, 128, 196)

        th = 0.05
        l = 0.25
        s = 0.75
        fontTh = 2

        horizontal = line(length=WORLD_WIDTH, color=c, thickness=th)
        vertical = line(length=WORLD_HEIGHT, color=c, thickness=th).rotate(90)

        # Horizontal
        for i in range(1, WORLD_WIDTH // 2):
            line(length=l, color=c, thickness=th).position(x=i).rotate(90)
            text(str(i), fontSize=s, fontThickness=fontTh).position(x=i, y=0.35)
        for i in range(1, WORLD_WIDTH // 2):
            line(length=l, color=c, thickness=th).position(x=-i).rotate(90)
