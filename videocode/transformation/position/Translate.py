#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation


class translate(Transformation):
    """
    `Translates` an `Input` by `x` `y`.

    This takes action on all frames instantly, there is no delay.

    For a movement over time, see `Move`.
    """

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
