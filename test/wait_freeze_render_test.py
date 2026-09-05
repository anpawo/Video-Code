#!/usr/bin/env python3

"""
Render-level regression test for the unified `wait(..., stop=...)` / `freeze()`
clock system.

This complements `fill_shader_test.py`'s event-shape checks with an actual
full-video render: a paint shader should keep moving during plain waits, hold
perfectly during `stop=Clock.PAINTS` / `freeze()`, then continue moving again
after each held span.

Run directly: `python3 test/wait_freeze_render_test.py`
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, needsRenderer, section, summary

FRAMES_PER_SEGMENT = 30
OUTPUT_WIDTH = 160
OUTPUT_HEIGHT = 90
FPS = 30

SCENE = """from videocode import *
BG = BLACK
Rectangle(width=16, height=9, fillColor=fire(speed=2.0, quality=0.8))
wait(1)
wait(1, stop=Clock.PAINTS)
wait(1)
freeze(1)
wait(1)
"""


def render_scene(scene_path: str, output_path: str, *flags: str) -> None:
    binary = os.path.abspath("video-code")
    if not os.path.exists(binary):
        raise FileNotFoundError(f"missing renderer binary: {binary}")

    cmd = [
        binary,
        "--file",
        scene_path,
        "--generate",
        output_path,
        "--width",
        str(OUTPUT_WIDTH),
        "--height",
        str(OUTPUT_HEIGHT),
        "--framerate",
        str(FPS),
        *flags,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def load_frames(video_path: str) -> list[np.ndarray]:
    cap = cv2.VideoCapture(video_path)
    frames: list[np.ndarray] = []
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(frame)
    finally:
        cap.release()
    return frames


def mean_diffs(frames: list[np.ndarray]) -> list[float]:
    return [float(np.mean(cv2.absdiff(a, b))) for a, b in zip(frames, frames[1:])]


def segment(values: list[float], start_frame: int) -> list[float]:
    start = start_frame
    end = start_frame + FRAMES_PER_SEGMENT - 1
    return values[start:end]


with tempfile.TemporaryDirectory() as tmp:
    scene_path = os.path.join(tmp, "scene.py")
    output_path = os.path.join(tmp, "wait-freeze.mp4")
    with open(scene_path, "w", encoding="utf-8") as f:
        f.write(SCENE)

    section("render")
    if not needsRenderer("wait/freeze needs a rendered video to measure frame differences"):
        summary()
        sys.exit(0)
    try:
        render_scene(scene_path, output_path)
        frames = load_frames(output_path)
        check("render succeeded and produced a readable video", len(frames) >= FRAMES_PER_SEGMENT * 5)
    except Exception as exc:
        check(f"render succeeded and produced a readable video ({exc})", False)
        summary()

    diffs = mean_diffs(frames)
    active1 = segment(diffs, 0)
    paused_paints = segment(diffs, 30)
    active2 = segment(diffs, 60)
    frozen_all = segment(diffs, 90)
    active3 = segment(diffs, 120)

    active_mean = float(np.mean(active1 + active2 + active3))
    paused_mean = float(np.mean(paused_paints))
    frozen_mean = float(np.mean(frozen_all))

    section("whole-video clock behavior")
    check("plain wait leaves the paint alive across the whole segment", float(np.mean(active1)) > 0.25)
    check("stop=Clock.PAINTS holds every consecutive frame in its whole segment", paused_mean < 0.02)
    check("plain motion resumes after the paint-only pause", float(np.mean(active2)) > 0.25)
    check("freeze() holds every consecutive frame in its whole segment", frozen_mean < 0.02)
    check("motion resumes again after freeze()", float(np.mean(active3)) > 0.25)
    check("active segments are materially more animated than the held segments", active_mean > max(paused_mean, frozen_mean) * 20)

    # ── the same clock, seen through a still and a sheet ─────────────────────
    # The agent pane's child cannot watch the video; it renders a PNG and reads
    # it back. So a still has to be the moment asked for, and a sheet's tiles
    # have to be exactly the stills of the times it claims — the label is in a
    # strip under each tile, which is what makes that byte-for-byte checkable.
    section("a still at a time, and a sheet of them")
    stills: dict[str, np.ndarray] = {}
    for at in ("0", "2", "2.5", "4"):
        path = os.path.join(tmp, f"still-{at}.png")
        render_scene(scene_path, path, "--from", at)
        stills[at] = cv2.imread(path)
    moved = int(np.count_nonzero(np.any(stills["0"] != stills["2.5"], axis=2)))
    check(f"--from 2.5 is not frame 0: {moved} of {OUTPUT_WIDTH * OUTPUT_HEIGHT} pixels differ", moved > OUTPUT_WIDTH * OUTPUT_HEIGHT // 2)
    held = int(np.count_nonzero(np.any(stills["2"] != stills["2.5"], axis=2)))
    check(f"half a second apart in a live stretch, --from 2 and --from 2.5 differ too: {held} pixels", held > OUTPUT_WIDTH * OUTPUT_HEIGHT // 2)

    sheet_path = os.path.join(tmp, "sheet.png")
    render_scene(scene_path, sheet_path, "--sheet", "3", "--from", "0", "--to", "4")
    sheet = cv2.imread(sheet_path)
    check(f"--sheet 3 is three tiles wide with a label strip under them (measured {sheet.shape[1]}x{sheet.shape[0]})", sheet.shape[1] == 3 * OUTPUT_WIDTH and sheet.shape[0] > OUTPUT_HEIGHT)
    for k, at in enumerate(("0", "2", "4")):
        tile = sheet[:OUTPUT_HEIGHT, k * OUTPUT_WIDTH:(k + 1) * OUTPUT_WIDTH]
        strip = sheet[OUTPUT_HEIGHT:, k * OUTPUT_WIDTH:(k + 1) * OUTPUT_WIDTH]
        check(f"tile {k} is the still at {at} s, pixel for pixel", bool(np.array_equal(tile, stills[at])))
        check(f"tile {k} carries a label (bright strip pixels: {int(np.count_nonzero(strip.max(axis=2) > 128))})", int(np.count_nonzero(strip.max(axis=2) > 128)) > 20)

    refused = subprocess.run([os.path.abspath("video-code"), "--file", scene_path, "--generate", os.path.join(tmp, "no.mp4"), "--sheet", "3"], capture_output=True, text=True)
    check("--sheet with a video output is refused, not silently a video", refused.returncode != 0 and "--sheet" in refused.stderr)

summary()
