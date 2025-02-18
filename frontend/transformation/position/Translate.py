#!/usr/bin/env python3

from frontend.transformation.Transformation import Transformation


class translate(Transformation):
    def __init__(self, x: int, y: int) -> None:
        """
        `Translates` an `Input` by `x` `y`.
        """
        self.x = x
        self.y = y
