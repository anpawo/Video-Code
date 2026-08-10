#!/usr/bin/env python3

"""
Assertion-based tests for the render size, as Python sees it.

The resolution is decided by --width/--height and handed down by C++ through
VC_SCREEN before videocode is imported. Python's whole job is to READ it and
build the world box from it. That contract is worth pinning because breaking
it doesn't crash — the world box and the renderer's surface simply stop
agreeing, and every shape lands off-centre.

Run directly: `python3 test/screen_test.py`
"""

import subprocess
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode.constants import (
    DEFAULT_SCREEN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WORLD_HEIGHT,
    WORLD_OFFSET_X,
    WORLD_OFFSET_Y,
    WORLD_TO_SCREEN_RATIO,
    WORLD_WIDTH,
)


def worldFor(env: str | None) -> tuple[float, ...]:
    """SCREEN_* / WORLD_* as a fresh interpreter sees them under VC_SCREEN."""
    code = (
        "import sys; sys.path.insert(0, '.');"
        "from videocode.constants import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT;"
        "print(SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)"
    )
    environment = {"PATH": "/usr/bin:/bin"}
    if env is not None:
        environment["VC_SCREEN"] = env
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=environment)
    return tuple(float(v) for v in out.stdout.split())


# ── the default ──────────────────────────────────────────────────────────────
section("no override — the 1920x1080 default")

check("DEFAULT_SCREEN is 1920x1080", DEFAULT_SCREEN == (1920, 1080))
check("an unset VC_SCREEN falls back to it", worldFor(None)[:2] == (1920.0, 1080.0))
check("this test process is at the default too", (SCREEN_WIDTH, SCREEN_HEIGHT) == (1920, 1080))

# ── the world box follows ────────────────────────────────────────────────────
section("the world box is derived, never declared")

check("world = screen / WORLD_TO_SCREEN_RATIO",
      (WORLD_WIDTH, WORLD_HEIGHT) == (SCREEN_WIDTH / WORLD_TO_SCREEN_RATIO, SCREEN_HEIGHT / WORLD_TO_SCREEN_RATIO))
check("the offsets are half the world box",
      (WORLD_OFFSET_X, WORLD_OFFSET_Y) == (WORLD_WIDTH / 2, WORLD_HEIGHT / 2))
check("the world unit is a fixed pixel count, so shapes keep their size across resolutions",
      WORLD_TO_SCREEN_RATIO == 120)

# ── C++ hands the size down ──────────────────────────────────────────────────
section("VC_SCREEN — what the renderer hands down")

check("a portrait render gives a portrait world", worldFor("1080x1920") == (1080.0, 1920.0, 9.0, 16.0))
check("a square render gives a square world", worldFor("1080x1080") == (1080.0, 1080.0, 9.0, 9.0))
check("a non-integer world is fine (4:5 -> 10x12.5)", worldFor("1200x1500") == (1200.0, 1500.0, 10.0, 12.5))
check("junk falls back to the default rather than raising", worldFor("nonsense")[:2] == (1920.0, 1080.0))

# ── a scene cannot change it ─────────────────────────────────────────────────
section("a scene has no say — only --width/--height do")

# Assigning SCREEN_WIDTH in a scene rebinds that scene's own global and
# nothing else: the surface is already allocated and the world box already
# built. The renderer never reads it back, which is why the flags are the only
# way in — this check pins that the module itself is not the source.
import videocode.constants as constants  # noqa: E402

constants.SCREEN_WIDTH = 640
check("assigning to constants.SCREEN_WIDTH does not move the world box",
      constants.WORLD_WIDTH == 1920 / WORLD_TO_SCREEN_RATIO)
constants.SCREEN_WIDTH = SCREEN_WIDTH

# setScreen IS the supported way to re-derive, used by C++ (applyScreenSize)
# when one process renders several sizes in a row — the visual suite.
constants.setScreen(1080, 1920)
check("setScreen re-derives the world box in place", constants.WORLD_WIDTH == 9.0 and constants.WORLD_HEIGHT == 16.0)
check("...and the star-imported copies elsewhere follow", constants.TOP_SIDE.y == 8.0)
constants.setScreen(1920, 1080)
check("...and back", constants.WORLD_WIDTH == 16.0 and constants.TOP_SIDE.y == 4.5)

summary()
