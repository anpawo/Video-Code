#!/usr/bin/env python3

#
# Types
#

from typing import Annotated, Any, Literal, TypeVar, Union

# screen width
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# unsigned int
uint = Annotated[int, "unsigned"]

# sides and align
type side = Literal["left", "right", "up", "down"]
type align = Literal["left", "right", "up", "down", "center"]

CENTER: align = "center"
LEFT: side | align = "left"
RIGHT: side | align = "right"
UP: side | align = "up"
DOWN: side | align = "down"

UL = [UP, LEFT]
UR = [UP, RIGHT]
DL = [DOWN, LEFT]
DR = [DOWN, RIGHT]


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
sec = float | int


# default parameters to specify that it's the default value
class default:
    """
    Default value to specify that a value is the default one and should be overriden by a given one.
    """

    def __init__(self, defaultValue: Any) -> None:
        self.defaultValue = defaultValue


type position = int | float
"""
Represents a coordinate position in a 2D space.

- `float`: `relative position` (ratio of window width/height).  
- `int`: `absolute position` (exact pixel x/y coordinates).  
"""
