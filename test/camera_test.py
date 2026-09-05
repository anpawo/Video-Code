#!/usr/bin/env python3

"""
The camera — one matrix over the whole picture, and what opts out of it.

`camera` moves and zooms the WHOLE frame. The claim that has to be measured is
that it is a magnification about the point the camera looks at, applied in the
vertex stage (a `Camera2D` push constant) — not a scale of the finished image
and not a crop. So this measures, in pixels:

- at zoom 1, a marker two world units to the right of the middle sits 240 px
  right of it (120 px per world unit);
- at zoom 2 it sits 480 px right — the distance doubled — and the marker itself
  is drawn twice as wide. A camera that only moved things would fail the second;
  one that only resized them would fail the first;
- what the camera looks at does not move: `camera.moveTo(x=2)` puts the world
  point (2, 0) in the middle of the frame;
- and a `pinToFrame()` marker does not move OR grow through any of it, which is
  the whole reason subtitles are legible.

Plus the thing the corpus barrier depends on: a scene that never mentions the
camera never gives it a slot in the stack, and one scene's camera never reaches
the next run (the editor bakes on every gesture, `--for` bakes once per shape).

Run directly: `python3 test/camera_test.py`
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, needsRenderer, section, summary

from PIL import Image

# Markers whose world positions are known: the middle, two units right, and one
# pinned to the frame down in the corner. `.position()`, not `.moveTo()` — the
# stills are exact frames, and an animation would blur the arithmetic.
MARKERS = """
from videocode import *

BG = BLACK

Square(side=0.4, fillColor=rgba(255, 0, 0), strokeColor=TRANSPARENT).position(0, 0)
Square(side=0.4, fillColor=rgba(0, 255, 0), strokeColor=TRANSPARENT).position(2, 0)
Square(side=0.4, fillColor=rgba(255, 255, 0), strokeColor=TRANSPARENT).position(-3, -3).pinToFrame()
"""

ZOOM = MARKERS + """
camera.over(duration=1).zoom = 2
wait(1)
"""

PAN = MARKERS + """
camera.moveTo(x=2, duration=1)
wait(1)
"""

RED, GREEN, YELLOW = (255, 0, 0), (0, 255, 0), (255, 255, 0)


def blob(path: str, color: tuple[int, int, int]) -> tuple[float, float, int]:
    """Centre (x, y) and drawn width, in pixels, of the one marker of `color`."""
    pixels = Image.open(path).convert("RGB").load()
    width, height = Image.open(path).size
    xs, ys = [], []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]  # type: ignore[index,misc]
            if all(abs(a - c) < 60 for a, c in zip((r, g, b), color)):
                xs.append(x)
                ys.append(y)
    if not xs:
        return (-1.0, -1.0, 0)
    return (sum(xs) / len(xs), sum(ys) / len(ys), max(xs) - min(xs) + 1)


def render(scene: str, out: str, at: str) -> None:
    subprocess.run(
        [os.path.abspath("video-code"), "--file", scene, "--generate", out, "--from", at],
        capture_output=True, text=True,
    )


def stackOf(source: str, tmp: str, name: str) -> dict:
    """Bake a scene the way C++ does, and hand back the stack it left."""
    from videocode.context import Context
    from videocode.serialize import execScene

    path = os.path.join(tmp, name)
    with open(path, "w") as f:
        f.write(source)
    execScene(path)
    return Context.stack


def claimsOn(stack: dict, index: int) -> set[str]:
    """Which channels an input was written on — the Create sentinel (-1) aside."""
    return {key
            for frame, shaders in stack.get(index, {}).items() if frame >= 0
            for key in shaders}


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        section("the camera takes a slot only when a scene moves it")

        plain = stackOf("from videocode import *\nSquare(side=1)\n", tmp, "plain.py")
        check("a scene that never mentions the camera has one input", len(plain) == 1)

        moved = stackOf("from videocode import *\nSquare(side=1)\ncamera.moveTo(x=2, duration=1)\n", tmp, "moved.py")
        check("moving it adds exactly one", len(moved) == 2)
        check("and its pan is an ordinary Position claim", "Position" in claimsOn(moved, 1))

        zoomed = stackOf("from videocode import *\nSquare(side=1)\ncamera.over(duration=1).zoom = 2\n", tmp, "zoomed.py")
        check("and its zoom an ordinary Scale claim", "Scale" in claimsOn(zoomed, 1))

        # The editor bakes on every gesture and `--for` bakes once per shape,
        # both in ONE interpreter — a camera left where the last run parked it
        # would pan a scene that never asked to be panned.
        after = stackOf("from videocode import *\nSquare(side=1)\n", tmp, "after.py")
        from videocode.input.Camera import camera

        check("a run leaves the camera where the next one expects it",
              len(after) == 1 and tuple(camera.meta.position) == (0, 0) and camera.zoom == 1)

        # Built last: these register inputs into whatever Context is current,
        # and every stackOf() above resets it.
        from videocode.input.Camera import Camera
        from videocode.input.shape.Rectangle import Square
        from videocode.shader.vertexShader.pinToFrame import pinToFrame

        check("the exported camera is a Camera", isinstance(camera, Camera))

        marker, square = pinToFrame(), Square(side=1)
        check("nothing is pinned until it is asked for", not marker.autodestroy(square))
        marker.modify(square)
        check("pinToFrame() marks the input", square.meta.pinnedToFrame)
        check("and a second application writes nothing", marker.autodestroy(square))

        if not needsRenderer("the camera measured in pixels"):
            summary()
            return

        section("zoom — a magnification about what the camera looks at")

        scene = os.path.join(tmp, "zoom.py")
        with open(scene, "w") as f:
            f.write(ZOOM)

        one, two = os.path.join(tmp, "one.png"), os.path.join(tmp, "two.png")
        render(scene, one, "0")
        render(scene, two, "1")

        red1, green1, pin1 = blob(one, RED), blob(one, GREEN), blob(one, YELLOW)
        red2, green2, pin2 = blob(two, RED), blob(two, GREEN), blob(two, YELLOW)

        check("at zoom 1, two world units are 240 px", abs((green1[0] - red1[0]) - 240) < 1)
        check("at zoom 2, the same two units are 480 px", abs((green2[0] - red2[0]) - 480) < 1)
        check("what the camera looks at does not move", abs(red2[0] - red1[0]) < 1 and abs(red2[1] - red1[1]) < 1)
        check("and the marker itself is drawn twice as wide", abs(green2[2] - 2 * green1[2]) <= 2)

        check("a pinToFrame() marker does not move", abs(pin2[0] - pin1[0]) < 1 and abs(pin2[1] - pin1[1]) < 1)
        check("nor grow", pin1[2] > 0 and pin2[2] == pin1[2])

        section("pan — the picture slides the other way")

        scene = os.path.join(tmp, "pan.py")
        with open(scene, "w") as f:
            f.write(PAN)

        before, moved_png = os.path.join(tmp, "before.png"), os.path.join(tmp, "moved.png")
        render(scene, before, "0")
        render(scene, moved_png, "1")

        greenBefore, pinBefore = blob(before, GREEN), blob(before, YELLOW)
        greenAfter, pinAfter = blob(moved_png, GREEN), blob(moved_png, YELLOW)

        centreX = Image.open(moved_png).size[0] / 2
        check("moveTo(x=2) puts the world point (2, 0) in the middle",
              abs(greenAfter[0] - (centreX - 0.5)) < 1)
        check("which is 240 px left of where it was", abs((greenBefore[0] - greenAfter[0]) - 240) < 1)
        check("and the pinned marker stayed put through the pan",
              abs(pinAfter[0] - pinBefore[0]) < 1 and abs(pinAfter[1] - pinBefore[1]) < 1)

    summary()


main()
