#!/usr/bin/env python3

"""
Assertion-based tests for `Image`/`Video` sizing when only ONE of
`width`/`height` is given — the other now follows the file's own aspect
ratio instead of being thrown away with the whole shape (which left the
picture at its raw pixel size, and silently dropped any `cornerRadius` or
stroke asked for in the same call).

Fixtures are synthesized at run time — a 300x100 PNG and a 320x180 mp4 —
the way `test/track_test.py` builds its clip: every checked-in PNG here is
square and `*.mp4` is gitignore'd repo-wide, so no committed asset can prove
aspect arithmetic.

Run directly: `python3 test/image_size_test.py`
"""

import atexit
import os
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, needsTool, section, summary

from videocode import *
from videocode.context import Context
from videocode.input.media.Image import _fitToRatio
import videocode.input.media.Image as ImageModule
import videocode.input.media.Video as VideoModule

from PIL import Image as PILImage

SRC_W, SRC_H = 300, 100
VID_W, VID_H = 320, 180


def temp(suffix: str) -> str:
    path = tempfile.NamedTemporaryFile(suffix=suffix, delete=False).name
    atexit.register(lambda: os.path.exists(path) and os.remove(path))
    return path


PNG = temp(".png")
PILImage.new("RGB", (SRC_W, SRC_H), "red").save(PNG)


def points(inp: Input) -> list:
    return Context.stack[inp.meta.index][-1]["args"]["points"]


# ── _fitToRatio — the arithmetic both media classes share ──────────────────
section("_fitToRatio — one number in, the other out")

check("width given, height follows the ratio", _fitToRatio(6, None, 300, 100) == (6, 2.0))
check("height given, width follows the ratio", _fitToRatio(None, 3, 320, 180) == (16 / 3, 3))
check("neither given falls back to the natural size", _fitToRatio(None, None, 240, 120) == (2.0, 1.0))


# ── Image — one dimension given ────────────────────────────────────────────
section("Image — one dimension given, the other from the file's ratio")

wide = Image(PNG, width=6)
check("height derived from the aspect ratio", wide.height == 2.0)
check("width kept as asked", wide.width == 6)
check("the shape reaches C++ (4 corners, 4 control points each)", len(points(wide)) == 16)
# `or [0]` so a regression that emits nothing FAILS this check instead of
# raising out of the suite and hiding every check below it.
xs = [p[0] for p in points(wide)] or [0]
ys = [p[1] for p in points(wide)] or [0]
check("the quad is 6 x 2 world units", (max(xs) - min(xs), max(ys) - min(ys)) == (6, 2.0))

tall = Image(PNG, height=2)
check("width derived from the aspect ratio", tall.width == 6.0)
check("height kept as asked", tall.height == 2)
check("the shape reaches C++", len(points(tall)) == 16)

# ── Image — the rounding/stroke that used to be dropped ────────────────────
section("Image — cornerRadius and stroke asked for in that same call")

rounded = Image(PNG, width=6, cornerRadius=30, strokeColor=WHITE, strokeWidth=0.1)
# `buildPoints` emits 4 control points per corner either way, so the count
# does NOT grow with rounding — what tells them apart is that no arc endpoint
# sits on the sharp corner any more.
check("rounded shape reaches C++", len(points(rounded)) == 16)
check("corners are arcs, not the sharp quad", points(rounded) != points(wide))
# Sharp corners repeat the vertex (arcStart == corner == arcEnd); a rounded
# one insets the arc endpoints away from it.
roundPts = points(rounded)
check("the arc starts away from the corner it rounds", len(roundPts) > 1 and roundPts[0] != roundPts[1])
entry = Context.stack[rounded.meta.index][-1]["args"]
check("strokeWidth carried", entry["strokeWidth"] == 0.1)

# ── Image — both given, and neither given, must not have moved ─────────────
section("Image — the two forms that already worked are untouched")

both = Image(PNG, width=4, height=4)
check("both given still stretch to that exact box", both.width == 4 and both.height == 4)
check(
    "both given emit the same sharp quad as ever",
    points(both) == [(0, 4), (0, 4), (0, 4), (2.0, 4.0), (4, 4), (4, 4), (4, 4), (4.0, 2.0),
                     (4, 0), (4, 0), (4, 0), (2.0, 0.0), (0, 0), (0, 0), (0, 0), (0.0, 2.0)],
)

bare = Image(PNG)
check("neither given leaves both None", bare.width is None and bare.height is None)
check("neither given emits no geometry (C++ draws the pixel quad)", points(bare) == [])

# The natural-size read is what makes a bare Image cost a file open — it must
# not start happening for the case that never paid it.
with patch.object(ImageModule.PILImage, "open", side_effect=AssertionError("opened the file")):
    stillBare = Image(PNG)
check("neither given reads no file at all", stillBare.width is None and points(stillBare) == [])

# ── Group — a member whose size Python can now answer ──────────────────────
section("Group — a sized Image no longer has a None extent")

try:
    pivot = Group(Image(PNG, width=2), Circle(radius=1).position(3, 0))._pivot()
except TypeError:
    pivot = None  # a member with a None extent — the crash this sizing removes
check("_pivot() returns a v2 instead of raising on None", isinstance(pivot, v2))

# ── Video — same rule, ffprobe instead of the PIL header ───────────────────
section("Video — one dimension given, the other from the source's ratio")

if needsTool("ffmpeg", "Video aspect-ratio sizing") and needsTool("ffprobe", "Video aspect-ratio sizing"):
    MP4 = temp(".mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"color=c=blue:s={VID_W}x{VID_H}:d=1:r=10", "-pix_fmt", "yuv420p", MP4],
        check=True,
    )

    clip = Video(MP4, height=3)
    check("width derived from the aspect ratio", clip.width == 16 / 3)
    check("height kept as asked", clip.height == 3)
    check("the shape reaches C++", len(points(clip)) == 16)

    clip2 = Video(MP4, width=8)
    check("height derived from the aspect ratio", clip2.height == 4.5)
    check("the shape reaches C++", len(points(clip2)) == 16)

# A bare Video must still cost nothing at construction — no ffprobe, which is
# also why it can name a file that does not exist yet.
with patch.object(VideoModule.subprocess, "run", side_effect=AssertionError("spawned ffprobe")):
    bareVid = Video("nowhere.mp4")
check("neither given spawns no ffprobe", bareVid.width is None and points(bareVid) == [])

# ── summary ──────────────────────────────────────────────────────────────────
summary()
