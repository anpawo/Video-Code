#!/usr/bin/env python3

#
# Constant
#

from sys import stderr
from .ty import *

# screen dimension
SCREEN_WIDTH = SW = 1920
SCREEN_HEIGHT = SH = 1080

# world dimension
WORLD_TO_SCREEN_RATIO = 120

WORLD_WIDTH = W = SCREEN_WIDTH // WORLD_TO_SCREEN_RATIO
WORLD_HEIGHT = H = SCREEN_HEIGHT // WORLD_TO_SCREEN_RATIO

WORLD_OFFSET_X = WORLD_WIDTH / 2
WORLD_OFFSET_Y = WORLD_HEIGHT / 2

# framerate
FRAMERATE = 30
SINGLE_FRAME = SF = 1 / FRAMERATE

# fmt: off
# direction
ORIGIN = v2[maybe[number]](0, 0)
UP     = v2[maybe[number]](None, 1)
DOWN   = v2[maybe[number]](None, -1)
RIGHT  = v2[maybe[number]](1, None)
LEFT   = v2[maybe[number]](-1, None)
# 3d
# OUT = 0, 0, 1
# IN = 0, 0, -1
UR: v2[maybe[number]] = UP + RIGHT
UL: v2[maybe[number]] = UP + LEFT
DR: v2[maybe[number]] = DOWN + RIGHT
DL: v2[maybe[number]] = DOWN + LEFT

TOP_SIDE    = v2[maybe[number]](None, WORLD_OFFSET_Y)
BOTTOM_SIDE = v2[maybe[number]](None, -WORLD_OFFSET_Y)
RIGHT_SIDE  = v2[maybe[number]](WORLD_OFFSET_X, None)
LEFT_SIDE   = v2[maybe[number]](-WORLD_OFFSET_X, None)

BL: v2[maybe[number]] = BOTTOM_SIDE + LEFT_SIDE
BR: v2[maybe[number]] = BOTTOM_SIDE + RIGHT_SIDE
TL: v2[maybe[number]] = TOP_SIDE + LEFT_SIDE
TR: v2[maybe[number]] = TOP_SIDE + RIGHT_SIDE


# colors
TRANSPARENT = rgba(0, 0, 0, 0)
WHITE       = rgba(255, 255, 255, 255)
GRAY        = rgba(128, 128, 128, 255)
BLACK       = rgba(0, 0, 0, 255)
RED         = rgba(255, 0, 0, 255)
GREEN       = rgba(0, 255, 0, 255)
BLUE        = rgba(0, 0, 255, 255)
# fmt: on
