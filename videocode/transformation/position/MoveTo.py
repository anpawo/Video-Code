#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation


class moveTo(Transformation):
    """
    `Moves` an `Input` by `x` `y`, you will arrive at `x` `y` at the last frame.

    The position of the `Input` changes over time.
    """

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
