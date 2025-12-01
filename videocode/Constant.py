#!/usr/bin/env python3

#
# Types
#

from typing import Annotated, Any, Literal, TypeVar, Union

# screen dimension
SCREEN_WIDTH = SW = 1920
SCREEN_HEIGHT = SH = 1080

MIDDLE = (SW * 0.5, SH * 0.5)

# Integer values
type uint = int
type uint8 = int

# Float values
type ufloat = float


# sides and align
type side = Literal["left", "right", "top", "bottom"]
type align = Literal["left", "right", "top", "bottom", "center"]

CENTER: align = "center"
LEFT: side | align = "left"
RIGHT: side | align = "right"
TOP: side | align = "top"
BOTTOM: side | align = "bottom"

UL = [TOP, LEFT]
UR = [TOP, RIGHT]
DL = [BOTTOM, LEFT]
DR = [BOTTOM, RIGHT]


# Colors
type rgba = tuple[uint8, uint8, uint8, uint8]

TRANSPARENT: rgba = (0, 0, 0, 0)
WHITE: rgba = (255, 255, 255, 255)
BLACK: rgba = (0, 0, 0, 255)
RED: rgba = (255, 0, 0, 255)
GREEN: rgba = (0, 255, 0, 255)
BLUE: rgba = (0, 0, 255, 255)


# time
type sec = Union[ufloat, uint]
type t = Union[ufloat, uint, default]


# default parameters to specify that it's the default value
class default:
    """
    Default value to specify that a value is the default one and should be overriden by a given one.
    """

    def __init__(self, defaultValue: Any) -> None:
        self.defaultValue = defaultValue

    def __str__(self) -> str:
        return f"default({self.defaultValue})"


def getValueByPriority(t: Any, duration: Any) -> sec:
    if hasattr(t, "duration") and isinstance(t.duration, int | float):
        return t.duration
    elif isinstance(duration, int | float):
        return duration
    elif hasattr(t, "duration") and isinstance(t.duration, default):
        return t.duration.defaultValue
    elif isinstance(duration, default):
        return duration.defaultValue
    else:
        raise ValueError(duration)


type number = int | float
"""
`int`  |  `float`
"""
type position = tuple[number, number]

type Index = int
type Url = str

FRAMERATE = FR = 30

SINGLE_FRAME = SF = 1 / FRAMERATE
"""
Framerate multiplicator to get one single frame.
"""
