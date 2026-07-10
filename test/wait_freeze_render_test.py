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
from helpers import check, section, summary

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


def render_scene(scene_path: str, output_path: str) -> None:
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

summary()
