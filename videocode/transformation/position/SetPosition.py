#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation
from videocode.Constant import *
from videocode.Global import Metadata


class setPosition(Transformation):
    """
    set the `x` and `y` of an `Input`.

    `integer` -> pixel value

    `float`   -> ratio of the width/height of the window

    `None`    -> doesn't change the position

    This takes action on all frames instantly, there is no delay.

    For a movement over time, see `moveTo`.
    """

    def __init__(self, x: int | float | None = None, y: int | float | None = None) -> None:
        self.x = int(x * SCREEN_WIDTH) if isinstance(x, float) else x
        self.y = int(y * SCREEN_HEIGHT) if isinstance(y, float) else y
        self.duration = 0.0

    def modificator(self, meta: Metadata):
        # Update the position of the Input
        if self.x is not None:
            meta.x = self.x
        if self.y is not None:
            meta.y = self.y
