#!/usr/bin/env python3

from videocode.Constant import *
from videocode.Global import Metadata
from videocode.transformation.Transformation import Transformation


class moveTo(Transformation):
    """
    `Moves` an `Input` to `x` `y`, you will arrive at `x` `y` at the last frame.

    The position of the `Input` changes over time.
    """

    def __init__(self, x: int | float | None = None, y: int | float | None = None) -> None:
        self.srcX: int
        self.srcY: int
        self.dstX = int(x * SCREEN_WIDTH) if isinstance(x, float) else x
        self.dstY = int(y * SCREEN_HEIGHT) if isinstance(y, float) else y

    def modificator(self, meta: Metadata):
        # Get the initial position of the Input
        self.srcX = meta.x
        self.srcY = meta.y

        # Update the position of the Input
        if self.dstX is not None:
            meta.x = self.dstX
        if self.dstY is not None:
            meta.y = self.dstY
