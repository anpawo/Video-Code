#!/usr/bin/env python3

#
# Types
#

from typing import Annotated, Literal, Union

# unsigned int
uint = Annotated[int, "unsigned"]


# sides
LEFT = "left"
RIGHT = "right"
UP = "up"
DOWN = "down"

type side = Literal["left", "right", "up", "down"]

# index
START = 0
END = -1
