#!/usr/bin/env python3

#
# Types
#

from typing import Any, Literal, Union

# screen dimension
SCREEN_WIDTH = SW = 1920
SCREEN_HEIGHT = SH = 1080

CENTER = (SW * 0.5, SH * 0.5)

# Integer values
type uint = int
type uint8 = int

# Float values
type ufloat = float

# Colors
type rgba = tuple[uint8, uint8, uint8, uint8]

TRANSPARENT: rgba = (0, 0, 0, 0)
WHITE: rgba = (255, 255, 255, 255)
BLACK: rgba = (0, 0, 0, 255)
RED: rgba = (255, 0, 0, 255)
GREEN: rgba = (0, 255, 0, 255)
BLUE: rgba = (0, 0, 255, 255)

# Time
type sec = Union[ufloat, uint]

# Numbers
type number = int | float
type Index = int
type Url = str

# Framerate Magic
FRAMERATE = FR = 30
SINGLE_FRAME = SF = 1 / FRAMERATE
"""
Framerate multiplicator to get one single frame.
"""

# Vector 2D
class v2[T]:
    def __init__(self, x: T, y: T) -> None:
        self.x: T = x
        self.y: T = y
