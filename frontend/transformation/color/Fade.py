#!/usr/bin/env python3

from frontend.transformation.Transformation import *

from frontend.Constant import *


class fade(Transformation):
    """
    `Fade` from `sides`.

    Modify `opacity` for a `Fade in` or a `Fade out`.

    Default: `Fade in`.
    """

    def __init__(self, sides: list[side] = ALL, startOpacity: uint = 0, endOpacity: uint = 255) -> None:
        self.sides = sides
        self.startOpacity = startOpacity
        self.endOpacity = endOpacity


class fadeIn:
    """
    `Fade in` from `sides`.
    """

    def __new__(cls, sides: list[side] = ALL) -> fade:
        return fade(sides, startOpacity=0, endOpacity=255)


class fadeOut:
    """
    `Fade out` from `sides`.
    """

    def __new__(cls, sides: list[side] = ALL) -> fade:
        return fade(sides, startOpacity=255, endOpacity=0)


# fadeFromLeft etc...
