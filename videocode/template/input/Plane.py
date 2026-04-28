#!/usr/bin/env python3


import math

from videocode import *


class Plane(Group):
    def __init__(
        self,
        animate=False,
        showNumbers=False,
    ) -> None:
        super().__init__(
            *[
                VerticalLine(
                    length=WORLD_HEIGHT,
                    rounded=False,
                ).position(x=i, y=0)
                for i in range(WORLD_WIDTH // -2 + 1, WORLD_WIDTH // 2)
            ],
            *[
                HorizontalLine(
                    length=WORLD_WIDTH,
                    rounded=False,
                ).position(x=0, y=i)
                for i in range(math.ceil(WORLD_HEIGHT / -2), math.ceil(WORLD_HEIGHT / 2))
            ],
        )
