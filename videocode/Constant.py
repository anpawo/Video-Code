#!/usr/bin/env python3

#
# Types
#

from typing import Annotated, Any, Literal, TypeVar, Union

# unsigned int
uint = Annotated[int, "unsigned"]

# modes
type mode = Literal["static", "dynamic"]

# sides
type side = Literal["left", "right", "up", "down"]

ALL: list[side] = []
LEFT: list[side] = ["left"]
RIGHT: list[side] = ["right"]
UP: list[side] = ["up"]
DOWN: list[side] = ["down"]

UL = UP + LEFT
UR = UP + RIGHT
DL = DOWN + LEFT
DR = DOWN + RIGHT


# index
START = 0
END = -1


# Colors
type RGBA = tuple[int, int, int, int]

TRANSPARENT: RGBA = (0, 0, 0, 0)
WHITE: RGBA = (255, 255, 255, 255)
RED: RGBA = (255, 0, 0, 255)
GREEN: RGBA = (0, 255, 0, 255)
BLUE: RGBA = (0, 0, 255, 255)


# time
sec = float


# default parameters to specify that it's the default value
class default:
    def __init__(self, defaultValue: Any) -> None:
        self.defaultValue = defaultValue


T = TypeVar("T")

Defaultable = Union[default, T]

# position as a ratio of the w, h or as a pixel x, y
type position = int | float
