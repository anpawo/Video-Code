#!/usr/bin/env python3

from frontend.transformation.Transformation import *

from frontend.Constant import *


class fade(Transformation):
    def __init__(self, sides: list[side] = ALL, startOpacity: uint = 0, endOpacity: uint = 255) -> None:
        """
        `Fade` from `side`.

        Modify `opacity` for a `Fade in` or a `Fade out`.
        """
        self.sides = sides
        self.startOpacity = startOpacity
        self.endOpacity = endOpacity
