#!/usr/bin/env python3

from videocode.Constant import *
from videocode.Global import Metadata
from videocode.transformation.Transformation import Transformation


class moveTo(Transformation):
    """
    move an `Input` to the position `x` and `y`.

    - `float`: `relative position` (ratio of window width/height).
    - `int`: `absolute position` (exact pixel x/y coordinates).
    - `None` doesn't change the position

    The movement takes action over the duration of the effect.

    For an instantaneous movement, see `setPosition`.
    """

    def __init__(self, x: int | float | None = None, y: int | float | None = None) -> None:
        self.srcX: int
        self.srcY: int
        self.dstX = int(x) if isinstance(x, float) else x
        self.dstY = int(y) if isinstance(y, float) else y

    def modificator(self, meta: Metadata):
        # Get the initial position of the Input
        self.srcX = meta.x
        self.srcY = meta.y

        # Update the position of the Input
        if self.dstX is not None:
            meta.x = self.dstX
        if self.dstY is not None:
            meta.y = self.dstY
