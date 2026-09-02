#!/usr/bin/env python3

"""
Being wrong on purpose — what the engine does when the script is not right.

TC-16 of the acceptance plan for the 09/09 test session, and the case nobody
had ever run: the Beta Test Plan covers eight features and none of them is
failure behaviour. The bar it sets is that a mistake produces a message a
person can act on, naming the input and the value that was wrong. A silent
no-op is worse than a crash; a crash with a clear message is acceptable; a
crash inside a library internal with no context is a defect.

Three things were failing that bar before this file existed:

- `Circle(radius=-1)` built a circle of radius 1. The sign vanished into
  cos/sin and the picture did not match the code, silently.
- `moveBy(y=1, duration=0)` wrote no frames at all — and neither did a
  one-frame animation, which emitted its starting value and never arrived.
- A missing image file threw a useful message wrapped in
  `libc++abi: terminating due to uncaught exception`, which reads like the
  runtime failing rather than the scene being wrong.

Run directly: `python3 test/error_behaviour_test.py`
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, needsRenderer, section, summary

from videocode import *
from videocode.constants import SINGLE_FRAME
from videocode.context import Context


section("a dimension that is not one is refused, by the name the author typed")

for call, wanted in (
    ("Circle(radius=-1)", "radius"),
    ("Square(side=-2)", "side"),
    ("Rectangle(width=1, height=-3)", "height"),
):
    try:
        eval(call)
        check(f"{call} is refused", False)
    except ValueError as e:
        # `Square(side=-2)` reporting a `width` sends the author looking for a
        # line they never wrote, so the word matters as much as the refusal.
        check(f"{call} is refused, naming `{wanted}`", wanted in str(e) and "-" in str(e))

check("a shape with honest dimensions is still built", Circle(radius=1).width == 2.0)


section("an animation arrives, however short it is")


def travelled(duration) -> bool:
    s = Square(side=1, fillColor=BLUE_C)
    s.position(0, 0)
    s.moveTo(x=5, duration=duration)
    return s.meta.position.x == 5.0


check("duration=0 moves at once instead of doing nothing", travelled(0))
check("a one-frame animation reaches its destination", travelled(SINGLE_FRAME))
check("and so do the longer ones", travelled(2 * SINGLE_FRAME) and travelled(0.4))


section("a file the scene does not have is reported, not aborted on")

if needsRenderer("the missing-file message comes from the renderer"):
    scene = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    scene.write('from videocode import *\nImage("nexiste_pas_42.png").position(0, 0).fadeIn()\nwait(1)\n')
    scene.close()
    out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    out.close()
    try:
        done = subprocess.run(
            ["./video-code", "--file", scene.name, "--generate", out.name],
            capture_output=True, text=True, timeout=300,
        )
        said = done.stdout + done.stderr
        check("it exits with a failure rather than aborting", done.returncode == 1)
        check("the message names the file", "nexiste_pas_42.png" in said)
        check("and does not read as the runtime giving up", "libc++abi" not in said and "terminating due to" not in said)
    finally:
        os.remove(scene.name)
        if os.path.exists(out.name):
            os.remove(out.name)

section("a script that does not run must not report a video")

if needsRenderer("a failed scene still reaching the encoder is a renderer question"):
    broken = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    broken.write("from videocode import *\nthis is not python(\n")
    broken.close()
    out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    out.close()
    try:
        done = subprocess.run(
            ["./video-code", "--file", broken.name, "--generate", out.name],
            capture_output=True, text=True, timeout=300,
        )
        said = done.stdout + done.stderr
        # It printed the SyntaxError all along. Nothing read it: the encoder ran
        # on an empty scene, the progress bar reached 100% of nothing, and the
        # process exited 0 holding 261 bytes of container with no stream in it.
        check("the syntax error is named", "SyntaxError" in said)
        check("and the render refuses instead of exiting 0", done.returncode != 0)
        check("no file is passed off as a video", os.path.getsize(out.name) < 1024)
    finally:
        os.remove(broken.name)
        if os.path.exists(out.name):
            os.remove(out.name)

summary()
