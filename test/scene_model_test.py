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
# A kind is the CHANNEL a call wrote, axis included — `Scale:x`, not `Scale`.
# An effect claims only what it was given, so the axis is part of the answer to
# "what did this call really write": a move in x that says `Position:x` is
# telling you it left y alone.
check("scaleTo owns the scale", any(k.startswith("Scale") for k in kinds["scaleTo"]))
check("rotateBy owns the rotation", "Rotation" in kinds["rotateBy"])
# A group re-emits position for every member on every frame it touches — that is
# what keeps them in formation — so both calls carry it. What tells them apart is
# the row's NAME, which is the call, and the kinds are there to say what a call
# really wrote when someone asks.
check("and the group's own bookkeeping is not hidden", any(k.startswith("Position") for k in kinds["rotateBy"]))

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

# ── An instant takes no time ───────────────────────────────────────────────
section("an instant written after a wait does not cost a frame")
# Measured before the fix: 61 frames, the second wait starting at 31. A `show`
# is a one-frame write, and `wait()` counted from the frame AFTER it.
created = model("from videocode import *\nwait(1)\nCircle()\nwait(1)\n")
check("wait(1); Circle(); wait(1) is two seconds", created["frames"] == 2 * FPS)
check("and the second wait starts where the first ended",
      [w["start"] for w in created["waits"]] == [0, FPS])

# Not a creation: any one-frame write did it — hide, a colour, a position.
hidden_late = model("from videocode import *\nr = Rectangle()\nwait(1)\nr.hide()\nwait(1)\n")
check("wait(1); r.hide(); wait(1) is two seconds", hidden_late["frames"] == 2 * FPS)
check("the hide sits on the first frame of the second wait",
      [w["start"] for w in hidden_late["waits"]] == [0, FPS])

steps = model("from videocode import *\n" + "wait(1)\nRectangle()\n" * 10 + "wait(1)\n")
check("ten `wait(1); Rectangle()` steps and a last wait are eleven seconds, not 340 frames",
      steps["frames"] == 11 * FPS)

# What must NOT move: a span still carries the cursor to its end, and a scene
# with no instant after a wait is what it always was.
spanned = model("from videocode import *\nr = Rectangle()\nwait(1)\nr.fadeOut(duration=1)\nwait(1)\n")
check("a one-second fade after a wait still pushes the next wait a second",
      spanned["frames"] == 3 * FPS and [w["start"] for w in spanned["waits"]] == [0, 2 * FPS])
plain = model("from videocode import *\nr = Rectangle()\nr.fadeOut(duration=1)\nwait(1)\n")
check("nothing instant after the wait: unchanged",
      plain["frames"] == 2 * FPS and [w["start"] for w in plain["waits"]] == [FPS])

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

# ── The project's own templates/ folder ──────────────────────────────────────
section("a templates/ folder in the project is listed beside the library's")
import contextlib
import io
import os
import tempfile

from videocode.serialize import effectCatalogue

project = tempfile.mkdtemp()
os.mkdir(os.path.join(project, "templates"))
with open(os.path.join(project, "templates", "LowerThird.py"), "w") as f:
    f.write(
        "from videocode import *\n"
        "from videocode.input.interface.Group import Group\n"
        "class LowerThird(Group):\n"
        '    """A name and a title, bottom left."""\n'
        "    def __init__(self, name: str, title: str = 'Guest', color: rgba = BLUE_C):\n"
        "        super().__init__(Text(text=name), Text(text=title, fillColor=color))\n"
        "def _helper():\n"
        "    return 1\n"
    )
with open(os.path.join(project, "templates", "presets.py"), "w") as f:
    f.write(
        "from videocode.template.effect.other.popIn import popIn\n"
        "def myPop():\n"
        '    """A small, springy pop."""\n'
        "    return popIn(scale=0.3)\n"
    )
with open(os.path.join(project, "templates", "Broken.py"), "w") as f:
    f.write("raise RuntimeError('half written')\n")

complaints = io.StringIO()
with contextlib.redirect_stderr(complaints):
    yours = {one["name"]: one for one in templateCatalogue(project)}
    presets = {one["name"]: one for one in effectCatalogue(project)}

check("the class is there", "LowerThird" in yours)
check("in a group of its own, apart from what shipped", yours["LowerThird"]["group"] == "yours")
check("with the import the scene will resolve", yours["LowerThird"]["module"] == "templates.LowerThird")
check("its fields are read off the signature",
      [p["name"] for p in yours["LowerThird"]["params"]] == ["name", "title", "color"])
check("and a colour default is still named",
      dict((p["name"], p["default"]) for p in yours["LowerThird"]["params"])["color"] == "BLUE_C")
check("what it says about itself is its docstring",
      yours["LowerThird"]["says"] == "A name and a title, bottom left.")
check("the name it needs is the one with no default", yours["LowerThird"]["required"] == ["name"])
check("what shipped is still there beside it", yours["Arrow"]["group"] == "template")

check("a preset is an effect", "myPop" in presets and presets["myPop"]["form"] == "effect")
check("with the module it lives in", presets["myPop"]["module"] == "templates.presets")
check("a private helper is nobody's business", "_helper" not in presets)

check("a broken file is left out", "Broken" not in yours)
check("and said, not raised", "templates/Broken.py" in complaints.getvalue()
      and "half written" in complaints.getvalue())

# The import the editor writes has to resolve from the project root — which is
# `sys.path[0]` when the editor runs — with no `__init__.py` in the folder.
sys.path.insert(0, project)
check("`from templates.LowerThird import LowerThird` resolves from the project root",
      __import__("templates.LowerThird", fromlist=["LowerThird"]).LowerThird.__name__ == "LowerThird")
sys.path.remove(project)

check("no folder, no fuss", all(one["group"] != "yours" for one in templateCatalogue(tempfile.mkdtemp())))

# ── Ce qu'une exécution laisse derrière elle ───────────────────────────────
section("a run leaves nothing behind for the next one")
# The editor runs a scene on every gesture. Anything a run leaves standing is
# read by the next one as if it belonged to it — and answers about a scene that
# no longer exists are worse than no answer.
from videocode.context import Context

before = len(Context.metas)
model("from videocode import *\nsquare = Square(side=1)\nsquare.fadeIn()\n")
once = len(Context.metas)
model("from videocode import *\nsquare = Square(side=1)\nsquare.fadeIn()\n")
twice = len(Context.metas)
check("the register of inputs does not grow run after run", once == twice)

model("from videocode import *\nsquare = Square(side=1)\nsquare.zIndex(50)\n")
check("the highest layer is this scene's", Context.maxZIndex() == 50)
model("from videocode import *\nsquare = Square(side=1)\nsquare.fadeIn()\n")
check("and a layer from a deleted line is gone with it", Context.maxZIndex() != 50)

# ── Quelle ligne, de quel fichier ──────────────────────────────────────────
section("a line belongs to a file")
# An element built by an imported module has a line, and it is a line of that
# module. The editor writes by line number into the document it has open, so
# without the file beside the number a gesture on such an element rewrites
# whatever the scene happens to say at that number.
with tempfile.TemporaryDirectory() as folder:
    module = os.path.join(folder, "titles.py")
    with open(module, "w") as out:
        out.write(
            "from videocode import *\n"
            "\n"
            "def banner():\n"
            "    made = Square(side=1)\n"
            "    made.fadeIn()\n"
            "    return made\n"
        )
    sys.path.insert(0, folder)
    try:
        far = model(
            "from videocode import *\n"
            "from titles import banner\n"
            "shape = banner()\n"
            "shape.moveBy(x=1)\n"
        )["elements"][0]
    finally:
        sys.path.remove(folder)
        sys.modules.pop("titles", None)

    check("the element says which file made it", far["file"] == module)
    calls = {effect["call"]: effect["file"] for effect in far["effects"]}
    check("the effect written in the module carries the module", calls["fadeIn"] == module)
    check("the effect written in the scene carries the scene", calls["moveBy"] == "scene_model_test.py")
    written = {point["call"]: point["file"] for point in far["points"]}
    check("each place a statement could go names its file too", written["fadeIn"] == module
          and written["moveBy"] == "scene_model_test.py")

summary()
