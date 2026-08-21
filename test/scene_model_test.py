#!/usr/bin/env python3

"""
Assertion-based tests for the model the EDITOR reads — `serialize.sceneModel`.

Not what the renderer draws: what the timeline is allowed to say about it. Three
things have to hold, or a gesture writes to the wrong place:

- every effect names the call that wrote it, so a row can be acted on;
- a clip lasts as long as the element is on screen, hiding included;
- every element carries the lines that already touched it, with the cursor each
  one left behind — which is what lets `hide(start=…)` be written at a chosen
  moment rather than at the end of the file.

Run directly: `python3 test/scene_model_test.py`
"""

import json
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode.serialize import execSource

FPS = 30


def model(source: str) -> dict:
    answer = execSource(source, "scene_model_test.py")
    # A scene that did not run answers with a message, and reading the model
    # anyway is how a test reports a bug in its own fixture as a bug in the code.
    if not answer["ok"]:
        raise AssertionError(answer["message"])
    return json.loads(answer["scene"])


def called(element: dict) -> list[str]:
    return [effect["call"] for effect in element["effects"]]


def span(element: dict, call: str) -> tuple[int, int]:
    for effect in element["effects"]:
        if effect["call"] == call:
            return effect["start"], effect["end"]
    raise AssertionError(f"no effect from {call!r}")


# ── Provenance ─────────────────────────────────────────────────────────────
section("every effect names the call that wrote it")
one = model(
    "from videocode import *\n"
    "square = Square(side=1)\n"
    "square.fadeIn()\n"
    "square.flush()\n"
    "square.moveBy(x=1)\n"
)["elements"][0]

check("the scene's words, not the renderer's", called(one) == ["fadeIn", "moveBy"])
check("fadeIn is on line 3", one["effects"][0]["line"] == 3)
check("moveBy is on line 5", one["effects"][1]["line"] == 5)
check("the shaders behind it are kept", one["effects"][0]["kinds"] == ["Opacity"])
check("they do not overlap", span(one, "fadeIn")[1] < span(one, "moveBy")[0])

section("a group writes several kinds from one call, and stays one row")
members = model(
    "from videocode import *\n"
    "square = Square(side=1)\n"
    "circle = Circle(radius=1)\n"
    "Group(square, circle).scaleTo(0.5, duration=1.2).rotateBy(180, duration=1.2)\n"
)["elements"]

check("both members report both calls",
      all(sorted(set(called(m))) == ["rotateBy", "scaleTo"] for m in members))
check("one row per call, not one per shader", len(members[0]["effects"]) == 2)
check("scaleTo owns the scale", "Scale" in dict(
    (e["call"], e["kinds"]) for e in members[0]["effects"])["scaleTo"])
check("rotateBy owns the rotation", dict(
    (e["call"], e["kinds"]) for e in members[0]["effects"])["rotateBy"] == ["Rotation"])

section("a row is the call's own animation, not the group's whole activity")
shorter = model(
    "from videocode import *\n"
    "square = Square(side=1)\n"
    "circle = Circle(radius=1)\n"
    "Group(square, circle).scaleTo(0.5, duration=0.5).rotateBy(180, duration=1.5)\n"
)["elements"][0]

start, end = span(shorter, "scaleTo")
check("half a second of scale reads as half a second", end - start + 1 == round(0.5 * FPS))
start, end = span(shorter, "rotateBy")
# It ENDS a second and a half in. It starts one frame late, and deliberately: at
# frame zero the rotation has not turned by anything yet, and a shader that
# changes nothing is dropped rather than written.
check("and the rotation ends where its own duration says", end == round(1.5 * FPS) - 1)
check("its first frame is the one that turns", start == 1)

# ── How long a clip is ─────────────────────────────────────────────────────
section("an element is on screen until something takes it off")
hidden = model(
    "from videocode import *\n"
    "square = Square(side=1)\n"
    "square.fadeIn()\n"
    "square.hide(start=1.5)\n"
    "wait(3)\n"
)["elements"][0]

check("it appears when the fade makes it visible", hidden["first"] == 1)
check("it lasts until the frame before the hide", hidden["last"] == round(1.5 * FPS) - 1)

section("nothing hides it, so the scene is what ends it")
open_ended = model(
    "from videocode import *\n"
    "square = Square(side=1)\n"
    "square.fadeIn()\n"
    "wait(3)\n"
)
check("it runs to the last frame of the scene",
      open_ended["elements"][0]["last"] == open_ended["frames"] - 1)

section("shown again after being hidden")
again = model(
    "from videocode import *\n"
    "square = Square(side=1)\n"
    "square.fadeIn()\n"
    "square.hide(start=1)\n"
    "square.show(start=2)\n"
    "wait(3)\n"
)
check("the clip covers the whole of it",
      again["elements"][0]["last"] == again["frames"] - 1)

# ── Where a new statement can go ───────────────────────────────────────────
section("every element carries the lines that touched it")
points = model(
    "from videocode import *\n"
    "square = Square(side=1)\n"
    "square.fadeIn()\n"
    "square.flush()\n"
    "square.moveBy(x=1)\n"
)["elements"][0]["points"]

check("one per line, in the order they ran", [p["line"] for p in points] == [3, 5])
check("each says what it called", [p["call"] for p in points] == ["fadeIn", "moveBy"])
check("the first counts from the start", points[0]["cursor"] == 0)
check("the second counts from where the flush left it",
      points[1]["cursor"] == round(0.4 * FPS))

section("a `hide` written from a point lands where it was asked to")
# What the editor computes: `start` is the moment it wants, minus the cursor the
# chosen line left behind. If the arithmetic here is wrong, a trimmed clip ends
# somewhere nobody asked for.
target = 40
start = (target - points[1]["cursor"]) / FPS
placed = model(
    "from videocode import *\n"
    "square = Square(side=1)\n"
    "square.fadeIn()\n"
    "square.flush()\n"
    "square.moveBy(x=1)\n"
    f"square.hide(start={start})\n"
    "wait(3)\n"
)["elements"][0]
check("the clip ends on the frame before it", placed["last"] == target - 1)

summary()
