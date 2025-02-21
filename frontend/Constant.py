#!/usr/bin/env python3

#
# Types
#

from typing import Annotated, Literal, Union

# unsigned int
uint = Annotated[int, "unsigned"]


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
