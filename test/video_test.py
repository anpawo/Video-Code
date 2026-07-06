#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Video`'s `startFrame`/`endFrame` trimming
(#92, "Video from a frame to another, not full") — verifies they're translated
into the `cuts` ranges that the C++ side already clamps/merges against the
source's actual frame count — and for `speedRamps` (video time remapping:
speed ramps / reverse / freeze-frame), which check the Python-side stack
shape and overlap validation. `speedRamps`' actual rate math
(`Video::mapToSourceIndex`'s piecewise segment evaluator on the C++ side) is
NOT exercised here — see the standalone C++ harness referenced in the PR/
report for that; this file only covers what the existing `cuts` tests already
cover the same way: the JSON shape handed to C++, not C++ execution.
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

# ── speedRamps -> no ramps leaves speedRamps untouched, cuts unaffected ─────
section("Video — no speedRamps leaves speedRamps empty and cuts untouched")
v = Video("video.py", cuts=[(5, 8)])
check("no speedRamps by default", v.speedRamps == [])
check("cuts still unaffected by the speedRamps addition", v.cuts == [(5, 8)])

# ── speedRamps -> preserved (sorted by playbackStart) ───────────────────────
section("Video — speedRamps preserved and sorted by playbackStart")
v = Video("video.py", speedRamps=[(50, 60, 2.0), (0, 10, -1.0)])
check("speedRamps sorted ascending by playbackStart", v.speedRamps == [(0, 10, -1.0), (50, 60, 2.0)])

# ── speedRamps -> freeze-frame segment (rate 0.0) ───────────────────────────
section("Video — freeze-frame speedRamp (rate 0.0) round-trips")
v = Video("video.py", speedRamps=[(20, 30, 0.0)])
check("freeze segment stored as-is", v.speedRamps == [(20, 30, 0.0)])

# ── speedRamps -> reverse segment (negative rate) ───────────────────────────
section("Video — reverse speedRamp (negative rate) round-trips")
v = Video("video.py", speedRamps=[(0, 15, -1.0)])
check("reverse segment stored as-is", v.speedRamps == [(0, 15, -1.0)])

# ── speedRamps -> non-1x speed segment ──────────────────────────────────────
section("Video — speed-up/slow-mo speedRamps round-trip")
v = Video("video.py", speedRamps=[(0, 10, 2.0), (10, 20, 0.5)])
check("speed-up and slow-mo segments stored as-is", v.speedRamps == [(0, 10, 2.0), (10, 20, 0.5)])

# ── speedRamps -> overlap in playback space raises ──────────────────────────
section("Video — overlapping speedRamps raise ValueError")
raised = False
try:
    Video("video.py", speedRamps=[(0, 10, 2.0), (5, 15, 0.5)])
except ValueError:
    raised = True
check("overlapping speedRamps rejected", raised)

# touching (non-overlapping) ranges are fine: [0,10) and [10,20) don't overlap
v = Video("video.py", speedRamps=[(0, 10, 2.0), (10, 20, 0.5)])
check("adjacent (touching) speedRamps are not considered overlapping", v.speedRamps == [(0, 10, 2.0), (10, 20, 0.5)])

# ── speedRamps -> composes with cuts/startFrame/endFrame independently ─────
# speedRamps live in the same playback-frame index space that startFrame/
# endFrame/cuts already produce for the rest of the engine, so on the Python
# side they're stored independently — no interaction/merging happens here;
# the C++ mapToSourceIndex piecewise evaluator is what actually composes them
# (a speed ramp's source anchor is computed via the plain cuts-only mapping of
# its playbackStart) — not exercised at this stack-shape level, see the
# standalone C++ harness for that composition being checked by execution.
section("Video — speedRamps stored independently of cuts/startFrame/endFrame")
v = Video("video.py", cuts=[(20, 25)], startFrame=10, endFrame=50, speedRamps=[(0, 5, -1.0)])
check("cuts translation unaffected by speedRamps", v.cuts == [(20, 25), (0, 10), (50, 2**31 - 1)])
check("speedRamps stored independently", v.speedRamps == [(0, 5, -1.0)])

# ── summary ──────────────────────────────────────────────────────────────────
summary()
