#!/usr/bin/env python3

from __future__ import annotations

#
# Constant
#

from enum import Enum, StrEnum
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


class Direction(Enum):
    """
    A cardinal screen direction, for entrance/exit/transition effects
    (`slideIn`, `wipeOut`, `push`, ...). The value is the unit vector in
    world coordinates (Y positive-up).

        rect.apply(slideIn(direction=Direction.BOTTOM))
        push(sceneA, sceneB, direction=Direction.LEFT)
    """

    LEFT = (-1.0, 0.0)
    RIGHT = (1.0, 0.0)
    TOP = (0.0, 1.0)
    BOTTOM = (0.0, -1.0)

    @property
    def vector(self) -> tuple[float, float]:
        """Unit direction vector in world coordinates."""
        return self.value

    @property
    def opposite(self) -> Direction:
        x, y = self.value
        return Direction((-x, -y))

    @property
    def side(self) -> str:
        """Lowercase side name — matches `crop()`'s per-side kwargs."""
        return self.name.lower()


class Axis(Enum):
    """Which axis an oscillating effect (`shake`) moves along."""

    X = "x"
    Y = "y"
    BOTH = "both"


class Clock(StrEnum):
    """
    The ambient clocks a `wait(n, stop=[...])` can pause — everything else
    (scheduled state: positions, colors, visibility) holds by itself during
    a gap. `freeze(n)` = a wait stopping ALL of them.

    - `VIDEOS`: Video playback.
    - `PAINTS`: shader fills (silk/fire/starNest/mathShader patterns).
    - `EFFECTS`: time-driven effect progress (vhs, glitch, lightSweep, ...).
    """

    VIDEOS = "videos"
    PAINTS = "paints"
    EFFECTS = "effects"


class UVMapping(StrEnum):
    """
    How a texture (`Image`/`Video`) is wrapped onto its shape. Values match
    the C++ parser in `BezierPath.cpp` (a `StrEnum`, so members serialize to
    the JSON stack as their plain string value).

    - `STRETCH` (default): bbox-normalized UVs — the texture is stretched to
      the shape's bounding box.
    - `RADIAL`/`CONIC`: polar UVs around the bbox center, mirroring
      `RadialGradient`/`ConicGradient`'s center/angle convention; `uvAngle`
      (degrees) rotates the angular origin.
    """

    STRETCH = "stretch"
    RADIAL = "radial"
    CONIC = "conic"


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
