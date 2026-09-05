#!/usr/bin/env python3

"""
The moments a scene named, in the file it renders — and on the terminal.

`timestamp("the build")` is already how an author jumps around while editing.
It is also, exactly, what a chapter is: a name and where it starts. So a render
writes them into the container, and prints them in the form a description box
takes.

Two things have to hold, or the feature is a claim nobody can check:

- what ffprobe reads back out of the file is what the scene said, with the
  right start and end — a `--from` render moves them rather than pointing
  outside the file it wrote;
- the printed list says when YouTube will ignore it, and never contradicts
  itself about the container it just wrote.

Run directly: `python3 test/chapters_test.py`
"""

import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, needsTool, section, summary

WIDTH, HEIGHT = 160, 90

SCENE = """
from videocode import *

timestamp("the opening")
square = Square(side=1)
square.fadeIn(duration=0.5)
wait(11)

timestamp("the build")
square.moveBy(x=2, duration=1)
wait(11)

timestamp("the end")
square.fadeOut(duration=0.5)
wait(11)
"""

CLOSE = """
from videocode import *

square = Square(side=1)
square.fadeIn(duration=0.5)
wait(2)
timestamp("late and short")
square.moveBy(x=1, duration=0.5)
wait(2)
"""


def render(scene: str, output: str, *flags: str) -> str:
    """The render's own stdout, with the colours and the progress bar taken off."""
    done = subprocess.run(
        [
            os.path.abspath("video-code"),
            "--file", scene,
            "--generate", output,
            "--width", str(WIDTH),
            "--height", str(HEIGHT),
            *flags,
        ],
        check=True, capture_output=True, text=True,
    )
    plain = re.sub(r"\033\[[0-9;]*m", "", done.stdout)
    return "\n".join(line for line in plain.split("\r")[-1].split("\n"))


def chapters(path: str) -> list[dict]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_chapters", "-of", "json", path],
        check=True, capture_output=True, text=True,
    )
    return json.loads(out.stdout).get("chapters", [])


if not needsTool("./video-code", "rendering a video needs the built binary"):
    summary()
    sys.exit(0)
if not needsTool("ffprobe", "reading chapters back needs ffprobe"):
    summary()
    sys.exit(0)

with tempfile.TemporaryDirectory() as tmp:
    scene = os.path.join(tmp, "scene.py")
    with open(scene, "w") as out:
        out.write(SCENE)

    # ── In the file ────────────────────────────────────────────────────────
    section("what the scene named is in the file it rendered")
    whole = os.path.join(tmp, "whole.mp4")
    said = render(scene, whole)
    marks = chapters(whole)

    check(f"three named moments, three chapters (got {len(marks)})", len(marks) == 3)
    check("in the order the scene says them",
          [m["tags"]["title"] for m in marks] == ["the opening", "the build", "the end"])
    check("the first one starts the file", float(marks[0]["start_time"]) == 0.0)
    check("each one runs until the next begins",
          all(marks[i]["end_time"] == marks[i + 1]["start_time"] for i in range(len(marks) - 1)))
    check(f"the last one runs to the end of the scene ({marks[-1]['end_time']}s of 35)",
          abs(float(marks[-1]["end_time"]) - 35.0) < 0.05)

    # ── On the terminal ────────────────────────────────────────────────────
    section("and printed in the form a description box takes")
    check("the list is printed under a heading", "Chapters" in said and "the build" in said)
    check("times are counted from the start, as m:ss", "0:00  the opening" in said)
    check("a list YouTube will accept is not complained about", "YouTube will show none" not in said)

    # ── A stretch of it ────────────────────────────────────────────────────
    section("a --from render moves them instead of pointing outside the file")
    part = os.path.join(tmp, "part.mp4")
    said = render(scene, part, "--from", "11", "--to", "24")
    marks = chapters(part)

    check("the moment before the range is gone",
          [m["tags"]["title"] for m in marks] == ["the build", "the end"])
    check("what is left starts at the top of the file", float(marks[0]["start_time"]) == 0.0)
    check("and the last ends where the render does",
          abs(float(marks[-1]["end_time"]) - 13.0) < 0.05)
    check("the printed list agrees with the file it wrote", "0:00  the build" in said)
    check("two chapters is one of YouTube's three rules, and it is said",
          "there are 2, and it wants three" in said)
    check("it does not contradict the 0:00 it just printed",
          "the first one is not at 0:00" not in said)

    # ── What it refuses to claim ───────────────────────────────────────────
    section("a container that cannot carry them says so")
    close = os.path.join(tmp, "close.py")
    with open(close, "w") as out:
        out.write(CLOSE)
    said = render(close, os.path.join(tmp, "close.mp4"))
    check("a moment that is not at the start is said to break the rule",
          "the first one is not at 0:00" in said and "under ten seconds" in said)
    check("and the file has it anyway", "in the file itself either way" in said)

    said = render(scene, os.path.join(tmp, "moving.gif"))
    check("a gif is told it carries none", "a .gif file carries no chapters of its own" in said)
    check("and is not told they are in it", "in the file itself either way" not in said)
    check("the list is printed all the same", "0:00  the opening" in said)

summary()
