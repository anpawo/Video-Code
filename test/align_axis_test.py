#!/usr/bin/env python3

"""
`align(x=…)` names ONE axis, and a render has to accept that.

An axis left out of an `align` reaches the stack as a hole — deliberately, so
that an x ramp and a y ramp compose instead of erasing each other, exactly as
`position` does. The renderer read both axes unconditionally, so the hole
arrived at the JSON layer as a number that was null and the whole render died
with `type must be number, but is null`.

A legal line of scene that renders an error instead of a picture is the worst
kind of defect this project has: `Text("x").align(x=0)` is what anyone writes
to left-align a label.

Run directly: `python3 test/align_axis_test.py`
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, needsTool, section, summary

ONE_AXIS = """
from videocode import *

# One axis named, the other left alone — the case that used to kill the render.
Rectangle(width=2, height=0.4, fillColor=BLUE_C, strokeColor=TRANSPARENT).align(x=0).position(-1, 0.4)
Text(text="gauche", fontSize=0.5, fillColor=WHITE).align(x=0).position(-1, -0.5)
wait(1)
"""


def render(scene: str, output: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as file:
        file.write(scene)
        path = file.name
    try:
        return subprocess.run(
            [os.path.abspath("video-code"), "--file", path, "--generate", output,
             "--width", "480", "--height", "270", "--from", "0.5"],
            capture_output=True, text=True,
        )
    finally:
        os.unlink(path)


if not needsTool("./video-code", "rendering needs the built binary"):
    summary()
    sys.exit(0)

with tempfile.TemporaryDirectory() as tmp:
    section("a claim that names one axis renders")
    out = os.path.join(tmp, "one.png")
    done = render(ONE_AXIS, out)

    check(f"the render succeeds (exit {done.returncode})", done.returncode == 0)
    check("and says nothing about a null", "must be number" not in (done.stdout + done.stderr))
    check("a file comes out of it", os.path.exists(out) and os.path.getsize(out) > 0)

    if os.path.exists(out):
        import cv2
        import numpy as np

        image = cv2.imread(out)
        ink = np.argwhere(image.max(axis=2) > 90)
        # Rendered at 480x270, which is a world 4 by 2.25 units wide — the
        # world does not rescale with the pixels, so the shapes are placed near
        # the origin to stay inside it.
        check(f"and something is drawn in it ({len(ink)} pixels of ink)", len(ink) > 200)

summary()
