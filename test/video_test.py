#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Video`'s `startFrame`/`endFrame` trimming
(#92, "Video from a frame to another, not full") — verifies they're translated
into the `cuts` ranges that the C++ side already clamps/merges against the
source's actual frame count.
Run directly: `python3 test/video_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Video

# ── no trimming -> no extra cuts ─────────────────────────────────────────────
section("Video — no startFrame/endFrame leaves cuts untouched")
v = Video("video.py")
check("no cuts", v.cuts == [])

v = Video("video.py", cuts=[(5, 8)])
check("explicit cuts preserved", v.cuts == [(5, 8)])

# ── startFrame only -> cut [0, startFrame) ──────────────────────────────────
section("Video — startFrame trims the head")
v = Video("video.py", startFrame=10)
check("head cut added", v.cuts == [(0, 10)])

v = Video("video.py", startFrame=0)
check("startFrame=0 adds no cut", v.cuts == [])

# ── endFrame only -> cut [endFrame, +inf) ───────────────────────────────────
section("Video — endFrame trims the tail")
v = Video("video.py", endFrame=50)
check("tail cut added", v.cuts == [(50, 2**31 - 1)])

# ── both -> head and tail cuts, plus any explicit cuts ──────────────────────
section("Video — startFrame and endFrame combine with explicit cuts")
v = Video("video.py", cuts=[(20, 25)], startFrame=10, endFrame=50)
check("head, explicit and tail cuts all present", v.cuts == [(20, 25), (0, 10), (50, 2**31 - 1)])

# ── summary ──────────────────────────────────────────────────────────────────
summary()
