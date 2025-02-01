#!/usr/bin/env python3

#
# Types
#

from typing import Annotated, Literal


# unsigned int
uint = Annotated[int, "unsigned"]


# sides
LEFT = 0
RIGHT = 1
UP = 2
DOWN = 3
ALL = 4

side = Literal[0] | Literal[1] | Literal[2] | Literal[3] | Literal[4]
