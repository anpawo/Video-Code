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
kinds = dict((e["call"], e["kinds"]) for e in members[0]["effects"])
check("scaleTo owns the scale", "Scale" in kinds["scaleTo"])
check("rotateBy owns the rotation", "Rotation" in kinds["rotateBy"])
# A group re-emits position for every member on every frame it touches — that is
# what keeps them in formation — so both calls carry it. What tells them apart is
# the row's NAME, which is the call, and the kinds are there to say what a call
# really wrote when someone asks.
check("and the group's own bookkeeping is not hidden", "Position" in kinds["rotateBy"])

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
check("and the rotation keeps its own length", end - start + 1 == round(1.5 * FPS))

section("two calls written to happen together start on the same frame")
# The one thing a bar must never do: a rotation writes no shader on its first
# frame — nothing has turned yet — and for a while the row began there instead of
# where the call did, one frame after the `scaleTo` beside it. A row is the CALL,
# and a call starts when it says it starts.
check("scaleTo and rotateBy start together",
      span(shorter, "scaleTo")[0] == span(shorter, "rotateBy")[0])

together = model(
    "from videocode import *\n"
    "square = Square(side=1)\n"
    "square.fadeIn(duration=0.5)\n"
    "square.moveBy(x=1, duration=0.5)\n"
)["elements"][0]
check("so do a fade and a move on the same cursor",
      span(together, "fadeIn")[0] == span(together, "moveBy")[0])
check("a call covers exactly its own duration",
      span(together, "moveBy")[1] - span(together, "moveBy")[0] + 1 == round(0.5 * FPS))

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

# ── What the editor can offer to place ─────────────────────────────────────
section("the catalogue is what the language actually exposes")
from videocode.serialize import templateCatalogue

catalogue = templateCatalogue()
byName = {one["name"]: one for one in catalogue}

check("it found something in every family",
      {one["group"] for one in catalogue} >= {"shape", "media", "template"})
check("a shape is there", "Square" in byName)
check("and a composite one", "Arrow" in byName)

check("what the star import gives needs no import line", byName["Square"]["module"] == "")
check("a template carries the module it lives in",
      byName["Arrow"]["module"] == "videocode.template.input.Arrow")

check("a Square can be placed with no answers", byName["Square"]["required"] == [])
check("a Text cannot be placed without its text", byName["Text"]["required"] == ["text"])
check("a Video needs its file", byName["Video"]["required"] == ["filepath"])

# The editor writes only what differs from the default, so a default it cannot
# spell is a field it would have to leave to the person. A colour is the case
# that matters: `RED_A` is what a person types, and `(199, 84, 80, 255)` is not.
check("a colour default is named, not printed",
      dict((p["name"], p["default"]) for p in byName["Circle"]["params"])["fillColor"] == "RED_A")
check("optional is about the signature, not about having a spelling",
      all(p["optional"] for p in byName["Square"]["params"]))

check("every name in it can actually be imported",
      all(one["module"] == "" or __import__(one["module"], fromlist=[one["name"]])
          for one in catalogue))

summary()
