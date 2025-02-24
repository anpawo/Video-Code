#!/usr/bin/env python3

from frontend.transformation.Transformation import *

from frontend.Constant import *


class fade(Transformation):
    def __init__(self, sides: list[side] = ALL, startOpacity: uint = 0, endOpacity: uint = 255) -> None:
        """
        `Fade` from `sides`.

        Modify `opacity` for a `Fade in` or a `Fade out`.

        Default: `Fade in`.
        """
        self.sides = sides
        self.startOpacity = startOpacity
        self.endOpacity = endOpacity


class fadeIn:
    def __new__(cls, sides: list[side] = ALL) -> fade:
        """
        `Fade in` from `sides`.
        """
        return fade(sides, startOpacity=0, endOpacity=255)


class fadeOut:
    def __new__(cls, sides: list[side] = ALL) -> fade:
        """
        `Fade out` from `sides`.
        """
        return fade(sides, startOpacity=255, endOpacity=0)


# fadeFromLeft etc...
