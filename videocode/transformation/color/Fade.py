#!/usr/bin/env python3

from typing import Optional
from videocode.transformation.Transformation import *

from videocode.Constant import *


class fade(Transformation):
    """
    `Fade` from `sides`.

    Modify `opacity` for a `Fade in` or a `Fade out`.

    Default: `Fade in`.
    """

    def __init__(
        self,
        *,
        startOpacity: uint = 0,
        endOpacity: uint = 255,
        sides: side | list[side] = [],
        affectTransparentPixel: bool = False,  # Text `Inputs` have a black transparent background, we don't want it to be shown.
    ):
        self.startOpacity = startOpacity
        self.endOpacity = endOpacity

        if isinstance(sides, list):
            self.sides = sides
        else:
            self.sides = [sides]

        self.affectTransparentPixel = affectTransparentPixel


class fadeIn:
    """
    `Fade in` from all `sides` if any and in `duration` second.
    """

    def __new__(cls, *, sides: side | list[side] = []) -> fade:
        return fade(startOpacity=0, endOpacity=255, sides=sides)


class fadeOut:
    """
    `Fade out` from `sides`.
    """

    def __new__(cls, *, sides: side | list[side] = []) -> fade:
        return fade(startOpacity=255, endOpacity=0, sides=sides)


# fadeFromLeft etc...
