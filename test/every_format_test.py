#!/usr/bin/env python3

"""
One scene, every format — `--for youtube,tiktok,square`.

The whole claim of the flag is that a shape is a RE-LAYOUT and not a crop: the
scene is run again inside the new frame, reads the world box it finds there
(`Split.AUTO`, `W`/`H`, `TOP_SIDE`) and puts things somewhere else. A crop or a
scale of the 16:9 render would be indistinguishable from the flag doing nothing,
so that is what this measures, in pixels:

- a marker sitting in the first panel of a `Split.AUTO` view is a quarter of the
  way ACROSS a youtube frame and halfway DOWN it, and the other way round in a
  tiktok one — the two axes swap, which no crop and no scale can do;
- the wide render, resized to the tall one's pixels, is nowhere near it.

And what the flag refuses is refused out loud: an unknown shape name, `--for`
with nothing to write to, `--width` quietly outranked.

Run directly: `python3 test/every_format_test.py`
"""

import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, needsTool, section, summary

from PIL import Image

# A marker in the FIRST panel of a view that follows the frame. `.position()`,
# not `.moveTo()`: the still is frame 0, and an animation has not moved yet.
SCENE = """
from videocode import *
from videocode.template.input.SplitView import SplitView

BG = BLACK

sv = SplitView(ratio=1, fillColor=TRANSPARENT, strokeWidth=0)
Square(side=0.6, fillColor=WHITE, strokeWidth=0).position(sv.a.cx, sv.a.cy)
wait(1)
"""

SHAPES = {"youtube": (1920, 1080), "tiktok": (1080, 1920), "square": (1080, 1080)}


def render(scene: str, output: str, *flags: str) -> subprocess.CompletedProcess[str]:
    done = subprocess.run(
        [os.path.abspath("video-code"), "--file", scene, "--generate", output, *flags],
        capture_output=True, text=True,
    )
    done.stdout = re.sub(r"\033\[[0-9;]*m", "", done.stdout.replace("\r", "\n"))
    done.stderr = re.sub(r"\033\[[0-9;]*m", "", done.stderr)
    return done


def markerAt(path: str) -> tuple[float, float]:
    """Where the white marker sits, as a fraction of the frame it is in."""
    frame = Image.open(path).convert("L")
    box = frame.point(lambda v: 255 if v > 200 else 0).getbbox()
    assert box is not None, f"no marker in {path}"
    return ((box[0] + box[2]) / 2 / frame.width, (box[1] + box[3]) / 2 / frame.height)


if not needsTool("./video-code", "rendering a scene needs the built binary"):
    summary()
    sys.exit(0)

with tempfile.TemporaryDirectory() as tmp:
    scene = os.path.join(tmp, "scene.py")
    with open(scene, "w") as out:
        out.write(SCENE)

    # ── One command, one file per shape ────────────────────────────────────
    section("one command writes one file per shape, its name in the filename")
    done = render(scene, os.path.join(tmp, "film.png"), "--for", "youtube,tiktok,square")

    check("it succeeds", done.returncode == 0)
    for shape, size in SHAPES.items():
        path = os.path.join(tmp, f"film-{shape}.png")
        check(f"{shape} is written, and named for the shape", os.path.exists(path))
        check(f"...at {size[0]}x{size[1]}", os.path.exists(path) and Image.open(path).size == size)

    # Everything below reads those files; without them the measurements are
    # tracebacks rather than the answer that the flag did not run.
    if any(not os.path.exists(os.path.join(tmp, f"film-{s}.png")) for s in SHAPES):
        summary()
        sys.exit(1)

    # ── The proof it is a re-layout ────────────────────────────────────────
    section("the scene lays itself out again — not a crop, not a scale")
    wide = markerAt(os.path.join(tmp, "film-youtube.png"))
    tall = markerAt(os.path.join(tmp, "film-tiktok.png"))
    box = markerAt(os.path.join(tmp, "film-square.png"))

    check(f"16:9 puts it in the left column ({wide[0]:.2f} across, {wide[1]:.2f} down)",
          wide[0] < 0.35 and abs(wide[1] - 0.5) < 0.05)
    check(f"9:16 puts it in the top row ({tall[0]:.2f} across, {tall[1]:.2f} down)",
          abs(tall[0] - 0.5) < 0.05 and tall[1] < 0.35)
    check(f"1:1 stacks like the tall one ({box[0]:.2f} across, {box[1]:.2f} down)",
          abs(box[0] - 0.5) < 0.05 and box[1] < 0.35)
    check("so the marker moved on BOTH axes, which no crop can do",
          abs(wide[0] - tall[0]) > 0.2 and abs(wide[1] - tall[1]) > 0.2)

    # And the cheapest fake of all — squash the wide render into the tall
    # one's pixels — puts the marker where the tall render has nothing at all.
    scaled = os.path.join(tmp, "squashed.png")
    Image.open(os.path.join(tmp, "film-youtube.png")).resize(SHAPES["tiktok"]).save(scaled)
    faked = markerAt(scaled)
    check(f"a wide render squashed to 1080x1920 lands it at {faked[0]:.2f}/{faked[1]:.2f}, not {tall[0]:.2f}/{tall[1]:.2f}",
          abs(faked[0] - tall[0]) > 0.2 or abs(faked[1] - tall[1]) > 0.2)

    # ── The progress line ──────────────────────────────────────────────────
    if needsTool("ffmpeg", "the per-shape progress line is printed by a video render"):
        section("each shape says which it is, on the line the renderer already prints")
        done = render(scene, os.path.join(tmp, "clip.mp4"), "--for", "youtube,square")
        said = done.stdout

        check("the first render names its shape and its place in the run",
              "clip-youtube.mp4" in said and "youtube, 1 of 2" in said)
        check("and so does the second", "clip-square.mp4" in said and "square, 2 of 2" in said)
        check("each one says the size it is actually rendering",
              "1920x1080 · 30 fps" in said and "1080x1080 · 30 fps" in said)

        done = render(scene, os.path.join(tmp, "lone.mp4"), "--for", "tiktok")
        check("a run of one is not numbered", "tiktok, 1 of 1" not in done.stdout and "· tiktok" in done.stdout)

    # ── What it refuses, out loud ──────────────────────────────────────────
    section("a shape it cannot make is said, never skipped")
    done = render(scene, os.path.join(tmp, "no.png"), "--for", "banana")
    check("an unknown shape is refused", done.returncode != 0)
    check("...and the ones it knows are named", "youtube, tiktok, square" in done.stderr)
    check("nothing was written", not os.path.exists(os.path.join(tmp, "no-banana.png")))

    done = subprocess.run(
        [os.path.abspath("video-code"), "--file", scene, "--for", "tiktok"],
        capture_output=True, text=True,
    )
    check("--for with nothing to write to is refused rather than dropped",
          done.returncode != 0 and "needs --generate" in done.stderr)

    done = render(scene, os.path.join(tmp, "over.png"), "-w", "800", "--height", "600", "--for", "tiktok")
    check("--width outranked by a shape is said", "not used" in done.stderr)
    check("...and the shape is what was rendered",
          Image.open(os.path.join(tmp, "over-tiktok.png")).size == SHAPES["tiktok"])

summary()
