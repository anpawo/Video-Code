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
        startTime: sec,
        endTime: sec | None,  # if None, the endTime is the last frame.
        sides: side | list[side] | None = None,
        affectTransparentPixel: bool = False,  # Text `Inputs` have a black transparent background, we don't want it to be shown.
    ):
        self.startOpacity = startOpacity
        self.endOpacity = endOpacity

        self.startTime = startTime
        self.endTime = endTime

        if sides is None:
            self.sides = []
        elif isinstance(sides, list):
            self.sides = sides
        else:
            self.sides = [sides]

        self.affectTransparentPixel = affectTransparentPixel


class fadeIn:
    """
    `Fade in` from all `sides` if any and in `duration` second.
    """

    def __new__(cls, *, sides: side | list[side] | None = None, duration: sec = 1) -> fade:
        return fade(startOpacity=0, endOpacity=255, startTime=0, endTime=duration, sides=sides)


class fadeOut:
    """
    `Fade out` from `sides`.
    """

    def __new__(cls, *, sides: side | list[side] | None = None, duration: sec = 1) -> fade:
        return fade(startOpacity=255, endOpacity=0, startTime=-duration, endTime=None, sides=sides)


# fadeFromLeft etc...
