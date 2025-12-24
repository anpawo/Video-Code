#!/usr/bin/env python3

from enum import Enum
from typing import Optional
from videocode.transformation.Transformation import *

from videocode.Constant import *


class side(Enum):
    All = 0
    Left = 1
    Right = 2
    Top = 3
    Bottom = 4


# TODO: Should be opacity
class fade(Effect):
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
        side: side = side.All,
        affectTransparentPixel: bool = False,  # Text `Inputs` have a black transparent background, we don't want it to be shown.
    ):
        self.startOpacity = startOpacity
        self.endOpacity = endOpacity

        if isinstance(side, list):
            self.sides = side
        else:
            self.sides = [side]

        self.affectTransparentPixel = affectTransparentPixel


# TODO: Should be templates
class fadeIn:
    """
    `Fade in` from all `sides` if any and in `duration` second.
    """

    def __new__(cls, *, sides: side = side.All) -> fade:
        return fade(startOpacity=0, endOpacity=255, side=sides)


class fadeOut:
    """
    `Fade out` from `sides`.
    """

    def __new__(cls, *, side: side = side.All) -> fade:
        return fade(startOpacity=255, endOpacity=0, side=side)


# fadeFromLeft etc...
