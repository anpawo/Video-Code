#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation
from videocode.Constant import *


class setPosition(Transformation):
    """
    set the `x` and `y` of all frames of an `Input`.

    `integer` -> pixel value
    `float`   -> ratio of the width/height of the window
    `None`    -> doesn't change the position

    This takes action on all frames instantly, there is no delay.

    For a movement over time, see `Move`.
    """

    def __init__(self, x: int | float | None = None, y: int | float | None = None) -> None:
        self.x = x
        self.y = y
        self.duration = 0.0
