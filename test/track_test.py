#!/usr/bin/env python3

"""
Assertion-based tests for motion tracking (Tier 3, "killer feature":
`text.attachTo(video.track(x, y))`).

Four parts:
  1. `TrackedPath` — basic container behavior (no video/cv2 involved).
  2. `Input.attachTo()` — emits one `Position` stack entry per tracked frame,
     offset by `offset` — reuses `position()`'s existing step-function
     mechanism, no video/cv2 involved.
  3. `_pixelToWorld()` — the pixel->world conversion math powering
     `Video.track()`, checked on known input/output pairs. Pure math, no
     video/cv2 involved.
  4. `Video.track()` end-to-end against a synthetic fixture video — a
     320x240/30fps/60-frame clip with a 20x20 white square whose top-left
     corner moves at an exact, known linear velocity, generated on the fly
     via `cv2.VideoWriter` into a temp file (NOT a checked-in asset: `*.mp4`
     is gitignore'd repo-wide, so a committed fixture would silently vanish
     for every clone/CI run — generating it here keeps the test portable and
     self-contained) — verifies real `cv2.calcOpticalFlowPyrLK` tracking
     agrees with the known ground-truth motion, and separately verifies the
     "hold last known-good position" fallback via a monkeypatched
     `cv2.calcOpticalFlowPyrLK` that reports every frame as lost.

Run directly: `python3 test/track_test.py`
"""

import atexit
import os
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.input.media.Video import _pixelToWorld

import cv2
import numpy as np

# Ground truth for the synthetic fixture built below: a 20x20 white square's
# top-left corner starts at (40, 100) and moves at 80 px/sec (== 80/30
# px/frame) purely horizontally, over 60 frames at 30fps.
SRC_W, SRC_H = 320, 240
NFRAMES = 60
X0, Y0 = 40.0, 100.0
VX = 80.0 / 30.0
SQUARE = 20


def buildSyntheticVideo(path: str) -> None:
    """A moving white square on black, with an exact, known linear velocity —
    see the module docstring for why this is generated on the fly rather than
    checked in as a fixture."""
    writer = cv2.VideoWriter(path, cv2.VideoWriter.fourcc(*"mp4v"), 30, (SRC_W, SRC_H))
    try:
        for f in range(NFRAMES):
            frameImg = np.zeros((SRC_H, SRC_W, 3), dtype=np.uint8)
            px = int(round(X0 + f * VX))
            cv2.rectangle(frameImg, (px, int(Y0)), (px + SQUARE, int(Y0) + SQUARE), (255, 255, 255), -1)
            writer.write(frameImg)
    finally:
        writer.release()


FIXTURE = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
buildSyntheticVideo(FIXTURE)
atexit.register(lambda: os.path.exists(FIXTURE) and os.remove(FIXTURE))


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


# ── TrackedPath — container behavior ────────────────────────────────────────
section("TrackedPath — structure")

path = TrackedPath({0: (0.0, 0.0), 5: (1.0, 2.0), 3: (0.5, -0.5)})
check("len() reflects frame count", len(path) == 3)
check("__getitem__ by frame", path[5] == (1.0, 2.0))
check("__contains__", 3 in path and 7 not in path)
check("iteration yields (frame, point) sorted by frame", list(path) == [(0, (0.0, 0.0)), (3, (0.5, -0.5)), (5, (1.0, 2.0))])

# ── attachTo — one Position stack entry per tracked frame ──────────────────
section("Input.attachTo() — emits one Position stack entry per tracked frame")

r = Rectangle(width=1, height=1)
p = TrackedPath({0: (1.0, 2.0), 3: (4.0, 5.0), 10: (6.0, 7.0)})
r.attachTo(p)
positionsByFrame = framesWith(r.meta.index, "Position")
check("one Position entry per tracked frame", set(positionsByFrame.keys()) == {0, 3, 10})
check("frame 0 carries (1, 2)", (positionsByFrame[0]["args"]["x"], positionsByFrame[0]["args"]["y"]) == (1.0, 2.0))
check("frame 3 carries (4, 5)", (positionsByFrame[3]["args"]["x"], positionsByFrame[3]["args"]["y"]) == (4.0, 5.0))
check("frame 10 carries (6, 7)", (positionsByFrame[10]["args"]["x"], positionsByFrame[10]["args"]["y"]) == (6.0, 7.0))

section("Input.attachTo() — offset shifts every tracked frame")

r2 = Rectangle(width=1, height=1)
r2.attachTo(p, offset=100)
positionsByFrame2 = framesWith(r2.meta.index, "Position")
check("frames shifted by offset", set(positionsByFrame2.keys()) == {100, 103, 110})

# ── _pixelToWorld — pure conversion math, known input/output pairs ─────────
section("_pixelToWorld — center pixel maps to the video's own position")

# width=8, height=6, video centered at world origin: center pixel (160,120)
# must map back to (0, 0) exactly, since fracX=fracY=0.5 zeroes both terms.
check("center pixel -> world origin", _pixelToWorld(160, 120, 320, 240, 8, 6, 0, 0) == (0.0, 0.0))

section("_pixelToWorld — corner pixels map to bbox edges")

# Top-left pixel (0,0): fracX=0 -> worldX = centerX - width/2 (left edge).
# Image y=0 is the TOP of the frame, and world Y is positive-upward, so it
# must map to the TOP edge of the bbox: worldY = centerY + height/2.
check("top-left pixel -> (left, top) world edge", _pixelToWorld(0, 0, 320, 240, 8, 6, 0, 0) == (-4.0, 3.0))

# Bottom-right pixel (320,240): fracX=1 -> right edge; fracY=1 -> bottom edge.
check("bottom-right pixel -> (right, bottom) world edge", _pixelToWorld(320, 240, 320, 240, 8, 6, 0, 0) == (4.0, -3.0))

section("_pixelToWorld — non-origin video position offsets the result")

check("center pixel with offset center -> that center", _pixelToWorld(160, 120, 320, 240, 8, 6, 2.0, -1.0) == (2.0, -1.0))
check("top-left pixel with offset center -> shifted left/top edge", _pixelToWorld(0, 0, 320, 240, 8, 6, 2.0, -1.0) == (-2.0, 2.0))

# ── Video.track() — real end-to-end verification against known ground truth ─
section("Video.track() — real cv2 tracking matches synthetic ground-truth motion")

WIDTH, HEIGHT = 8.0, 6.0
vid = Video(FIXTURE, width=WIDTH, height=HEIGHT)
trackedPath = vid.track(X0, Y0, startFrame=0, endFrame=NFRAMES)

check("TrackedPath spans every frame from 0 to NFRAMES-1", set(trackedPath.positions.keys()) == set(range(NFRAMES)))

maxPixelErr = 0.0
maxWorldErr = 0.0
for f in range(NFRAMES):
    expectedPx = (X0 + f * VX, Y0)
    expectedWorld = _pixelToWorld(expectedPx[0], expectedPx[1], SRC_W, SRC_H, WIDTH, HEIGHT, 0.0, 0.0)
    actualWorld = trackedPath[f]
    worldErr = ((actualWorld[0] - expectedWorld[0]) ** 2 + (actualWorld[1] - expectedWorld[1]) ** 2) ** 0.5
    maxWorldErr = max(maxWorldErr, worldErr)
    # equivalent pixel-space error, for a human-readable number
    pixelErr = worldErr / (WIDTH / SRC_W)
    maxPixelErr = max(maxPixelErr, pixelErr)

print(f"    max world-unit error over {NFRAMES} frames: {maxWorldErr:.5f}  (~{maxPixelErr:.2f} px equivalent)")
check("tracked motion agrees with ground truth within 3px-equivalent tolerance", maxPixelErr < 3.0)

section("Video.track() — endFrame=None defaults to the full source length")

fullPath = vid.track(X0, Y0, startFrame=0)
check("endFrame=None tracks through the last frame", max(fullPath.positions.keys()) == NFRAMES - 1)

# ── Video.track() — lost-track fallback holds the last known-good position ─
section("Video.track() — lost tracking holds the last known-good position")

with patch.object(cv2, "calcOpticalFlowPyrLK") as mockLK:
    # Every call reports the point unmoved but status=0 (lost) — the
    # returned pts value must be ignored in favor of holding the previous one.
    def fakeLK(prevGray, gray, pts, _out, **kwargs):
        bogus = pts + 999.0  # if this leaked through, positions would diverge
        return bogus, np.array([[0]], dtype=np.uint8), np.array([[0.0]], dtype=np.float32)

    mockLK.side_effect = fakeLK
    lostPath = vid.track(X0, Y0, startFrame=0, endFrame=5)

startWorld = lostPath[0]
check("lost tracking holds frame 0's position for every later frame", all(lostPath[f] == startWorld for f in range(1, 5)))

# ── summary ──────────────────────────────────────────────────────────────────
summary()
