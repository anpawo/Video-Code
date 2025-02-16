#!/usr/bin/env python3

from frontend.transformation._Transformation import Transformation


class move(Transformation):
    def __init__(self, x: int, y: int) -> None:
        """
        `Moves` an `Input` by `x` `y`, you will arrive at `x` `y` at the last frame.
        """
        self.x = x
        self.y = y
