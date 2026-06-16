#!/usr/bin/env python3

from __future__ import annotations

#
# Constant
#

from sys import stderr
from videocode.ty import *
import videocode.utils.logger as logger

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
SINGLE_FRAME = SF = FRAME_TO_SEC = 1 / FRAMERATE

# Reserved zIndex sentinel for background elements (e.g. Plane's grid — see
# Input.background()). User content always has zIndex >= 0 (sendToBack/
# sendBackward clamp to that floor), so this value is never produced by
# normal layer-order operations and unambiguously marks "background".
# Excluded from Context.maxZIndex/minZIndex/zIndexAbove/zIndexBelow.
BACKGROUND_Z_INDEX = -1

# fmt: off
# direction
ORIGIN = v2(0, 0)
UP     = v2(None, 1)
DOWN   = v2(None, -1)
RIGHT  = v2(1, None)
LEFT   = v2(-1, None)
# 3d
# OUT = 0, 0, 1
# IN = 0, 0, -1
UR: v2[maybe[number], maybe[number]] = UP + RIGHT
UL: v2[maybe[number], maybe[number]] = UP + LEFT
DR: v2[maybe[number], maybe[number]] = DOWN + RIGHT
DL: v2[maybe[number], maybe[number]] = DOWN + LEFT

TOP_SIDE    = v2(None, WORLD_OFFSET_Y)
BOTTOM_SIDE = v2(None, -WORLD_OFFSET_Y)
RIGHT_SIDE  = v2(WORLD_OFFSET_X, None)
LEFT_SIDE   = v2(-WORLD_OFFSET_X, None)

BL: v2[maybe[number], maybe[number]] = BOTTOM_SIDE + LEFT_SIDE
BR: v2[maybe[number], maybe[number]] = BOTTOM_SIDE + RIGHT_SIDE
TL: v2[maybe[number], maybe[number]] = TOP_SIDE + LEFT_SIDE
TR: v2[maybe[number], maybe[number]] = TOP_SIDE + RIGHT_SIDE


# colors
TRANSPARENT = rgba(000, 000, 000, 0)
WHITE       = rgba(255, 255, 255)
BLACK       = rgba(000, 000, 000)
GRAY        = WHITE | BLACK
GRAY_10     = rgba(10, 10, 10)

RED         = rgba(255, 0, 0)
GREEN       = rgba(0, 255, 0)
BLUE        = rgba(0, 0, 255)
YELLOW      = rgba(255, 255, 0)

RED_A       = rgba("#FC6255")
RED_B       = rgba("#ED7F7B")

GREEN_A     = rgba("#9ADF8E")

BLUE_A      = rgba("#58C4DD") # light blue
BLUE_B      = rgba("#0B142B") # very dark blue
BLUE_C      = rgba("#69A5F1")
# fmt: on

DEBUG = logger.Logger(prefix="Debug", color=logger.TEXT_GREEN)
