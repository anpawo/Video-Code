#!/usr/bin/env python3


import math


from videocode import *


class Plane(Group):
    def __init__(
        self,
        center=False,
    ) -> None:
        transparent = 0.05

        super().__init__(
            Rectangle(
                width=WORLD_WIDTH,
                height=WORLD_HEIGHT,
                fillColor=BLUE_B,
                strokeColor=TRANSPARENT,
            ),
            *[
                VerticalLine(
                    length=WORLD_HEIGHT,
                    strokeWidth=0.01,
                    rounded=False,
                    fillColor=WHITE | transparent,
                ).position(x=i, y=0)
                for i in floatRange(WORLD_WIDTH // -2, WORLD_WIDTH // 2, 1 / 3)
            ],
            *[
                HorizontalLine(
                    length=WORLD_WIDTH,
                    strokeWidth=0.01,
                    rounded=False,
                    fillColor=WHITE | transparent,
                ).position(x=0, y=i)
                for i in floatRange(math.ceil(WORLD_HEIGHT / -2) - 1, math.ceil(WORLD_HEIGHT / 2), 1 / 3)
            ],
            *([Dot().position(0, 0)] if center else []),
        )
