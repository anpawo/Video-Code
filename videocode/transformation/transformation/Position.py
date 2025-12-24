#!/usr/bin/env python3

from videocode.Constant import *
from videocode.Global import Metadata
from videocode.transformation.Transformation import Transformation


class position(Transformation):
    """
    set the position `x` and `y` of an `Input`.

    - `None` doesn't change the position

    This takes action on all frames instantly, there is no delay.

    For a movement over time, see `moveTo`.
    """

    def __init__(self, x: number | None = None, y: number | None = None) -> None:
        self.x = x
        self.y = y

    def modificator(self, meta: Metadata):
        # Update the position of the Input
        if self.x is not None:
            meta.position.x = self.x
        else:
            self.x = meta.position.x

        if self.y is not None:
            meta.position.y = self.y
        else:
            self.y = meta.position.y
