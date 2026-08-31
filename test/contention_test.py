#!/usr/bin/env python3

"""
Assertion-based tests for `Context.contendedKeys()`: two statements writing the
same key over the same frames, where the order the lines were typed in is what
decides the video.
Run directly: `python3 test/contention_test.py`
"""

import contextlib
import io
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Context
from videocode.serialize import execSource


def contentions(body: str) -> list[dict]:
    # The run PRINTS what it finds; this reads the same finding as data.
    with contextlib.redirect_stderr(io.StringIO()):
        execSource("from videocode import *\n\ns = Square(side=1)\n" + body + "\nwait(3)\n", "contention_test_scene.py")
    return Context.contendedKeys()


# ── What it must catch ──────────────────────────────────────────────────────
# Two animations over the same frames on one key do not blend: a frame holds
# one entry per key, so the later call erases the earlier one wherever they
# meet, and swapping the two lines gives a different video.
section("contendedKeys — two animations fighting over one key")

# The example is two moves on the SAME axis. It used to be x against y — until
# an effect began claiming only the axis it was given, which made those two
# compose. Two claims on one axis is what is left, and it is the real case.
fight = contentions("s.moveTo(x=2, duration=1)\ns.moveBy(x=1, duration=1)")
check("the pair is reported", len(fight) == 1)
check("named by channel, axis included", fight and fight[0]["key"] == "Position:x")
check("both call sites are named", fight and {fight[0]["a"]["call"], fight[0]["b"]["call"]} == {"moveTo", "moveBy"})
check("with the frames they share", fight and fight[0]["frames"] == 30)

check(
    "reported whichever order the two lines are in",
    len(contentions("s.moveBy(x=1, duration=1)\ns.moveTo(x=2, duration=1)")) == 1,
)
check(
    "partial overlap counts too",
    len(contentions("s.moveTo(x=2, duration=1)\ns.moveBy(x=1, start=0.5, duration=1)")) == 1,
)

# ── What it must NOT catch ──────────────────────────────────────────────────
# The repository's 52 scenes report nothing, and these are the shapes that is
# made of. A rule that cries wolf on how every scene is written is a rule
# nobody reads.
section("contendedKeys — silent on how a scene is normally written")

check("different keys never contend", not contentions("s.moveTo(x=2, duration=1)\ns.fadeIn(duration=1)"))
check(
    "a construction call is the animation's starting value, not a rival",
    not contentions("s.position(x=-2)\ns.moveTo(x=2, duration=1)"),
)
check(
    "flush() puts them in separate windows",
    not contentions("s.moveTo(x=2, duration=1)\ns.flush()\ns.moveBy(x=1, duration=1)"),
)
check(
    "back to back, sharing only the handover frame",
    not contentions("s.moveTo(x=2, duration=1)\ns.moveBy(x=1, start=1, duration=1)"),
)
check("one statement is never its own rival", not contentions("s.moveTo(x=2, duration=1)"))

# ── One emitter call is one statement ───────────────────────────────────────
# The bug this guards: `ease()` — and `over()`, `easeTogether`, `fillIn` on top
# of it — writes a frame at a time, so a ramp arrives as N statements one frame
# long. Counting those raw made the whole of paint animation invisible here:
# every span was a single frame, and a single frame is rightly never contended.
# Two `over().fillColor` overlapping by half a second reported nothing at all.
section("contendedKeys — a frame-by-frame emitter is still one statement")


def painted(body: str) -> list[dict]:
    with contextlib.redirect_stderr(io.StringIO()):
        execSource(
            "from videocode import *\n\nr = Rectangle(width=2, height=2, fillColor=BLUE_B)\n" + body + "\nwait(3)\n",
            "contention_test_paint.py",
        )
    return Context.contendedKeys()


check("two overlapping fillColor ramps are reported", len(painted("r.over(duration=0.5).fillColor = RED_B\nr.over(duration=0.5).fillColor = WHITE")) == 1)
check("named by the channel, not by the shader class", painted("r.over(duration=0.5).fillColor = RED_B\nr.over(duration=0.5).fillColor = WHITE")[0]["key"] == "Args:fillColor")
check("fillColor and strokeColor are different channels", not painted("r.over(duration=0.5).fillColor = RED_B\nr.over(duration=0.5).strokeColor = WHITE"))

# ── An axis is a channel ────────────────────────────────────────────────────
# Since an effect claims only the axis it was given, two effects on different
# axes compose — so calling them a conflict would be crying wolf on the very
# thing the claim model exists to allow.
section("contendedKeys — x and y are different channels")

check("moveTo(x) and moveBy(y) do not contend", not contentions("s.moveTo(x=2, duration=1)\ns.moveBy(y=3, duration=1)"))
check("moveTo(x) twice does", len(contentions("s.moveTo(x=2, duration=1)\ns.moveTo(x=5, duration=1)")) == 1)
check("and it is named by the axis", contentions("s.moveTo(x=2, duration=1)\ns.moveTo(x=5, duration=1)")[0]["key"] == "Position:x")

# ── What a group works out is not a statement about a member ────────────────
# A group re-emits its whole window on every apply, so two chained animations
# look from the outside like two statements fighting over one key — when
# `_rigidTimeline` has already composed them per channel. But a member written
# BY HAND during a group's window is a real conflict, and must still be said.
section("contendedKeys — a group's own working-out is not a rival")


def grouped(body: str) -> list[dict]:
    with contextlib.redirect_stderr(io.StringIO()):
        execSource(
            "from videocode import *\n\na = Square(side=0.4).position(x=-1)\nb = Square(side=0.4).position(x=1)\ng = Group(a, b)\n" + body + "\nwait(3)\n",
            "contention_test_group.py",
        )
    return Context.contendedKeys()


check("chained group animations are not a conflict", not grouped("g.scaleTo(2, duration=1).rotateBy(90, duration=1)"))
check("a member written by hand during a group window IS", len(grouped("g.rotateBy(90, duration=1)\nb.moveBy(y=1, duration=1)")) == 1)

# ── A line that reaches back behind one written above it ────────────────────
# An animation reads where to start from the CURSOR, which is the right answer
# as long as the lines are written in the order they play. Give a `start=` that
# opens behind a line already written and the cursor has been carried past it:
# measured, `moveTo(x=5, start=2)` then `moveTo(x=2)` sends x from 4.99 DOWN to
# 2 over the first second, where the same two lines the other way round send it
# from 0 up to 2. Same intent, two videos.
section("backdatedWrites — a start= that opens behind a line written above it")


def backdated(body: str) -> list[dict]:
    with contextlib.redirect_stderr(io.StringIO()):
        execSource("from videocode import *\n\ns = Square(side=1)\n" + body + "\nwait(4)\n", "contention_test_order.py")
    return Context.backdatedWrites()


check("written in the order they play: nothing to say", not backdated("s.moveTo(x=2, duration=1)\ns.moveTo(x=5, start=2, duration=1)"))
check("written the other way round: reported", len(backdated("s.moveTo(x=5, start=2, duration=1)\ns.moveTo(x=2, duration=1)")) == 1)
check(
    "and it names the line that reaches back",
    backdated("s.moveTo(x=5, start=2, duration=1)\ns.moveTo(x=2, duration=1)")[0]["b"]["line"] == 5,
)
check(
    "a different channel is not affected by it",
    not backdated("s.moveTo(x=5, start=2, duration=1)\ns.moveTo(y=2, duration=1)"),
)

# What the two orders actually produce, so the test says why it cares.
def firstX(body: str) -> float:
    with contextlib.redirect_stderr(io.StringIO()):
        execSource("from videocode import *\n\ns = Square(side=1)\n" + body + "\nwait(4)\n", "contention_test_order.py")
    frames = sorted(f for f in Context.stack[0] if f != -1 and "Position" in Context.stack[0][f])
    return Context.stack[0][frames[0]]["Position"]["args"]["x"]


check(
    "the two orders really do differ — that is the whole point",
    abs(firstX("s.moveTo(x=2, duration=1)\ns.moveTo(x=5, start=2, duration=1)")
        - firstX("s.moveTo(x=5, start=2, duration=1)\ns.moveTo(x=2, duration=1)")) > 1.0,
)

# ---------------------------------------------------------------------------
section("channelKey — the name one piece of state answers to, spelled once")

check("an ordinary shader is its own class", Context.channelKey("Position", None) == "Position")
check("an args shader is named by its attribute", Context.channelKey("Args", "fillColor") == "Args:fillColor")
check("two attributes are two channels",
      Context.channelKey("Args", "fillColor") != Context.channelKey("Args", "strokeColor"))

# The reason this function exists rather than the rule being inlined twice: the
# key a frame is STORED under (Context.apply) and the key two statements are
# judged rivals by (Input.apply) must be the same string. They used to be two
# copies of one rule, agreeing by coincidence — so this asserts they agree, not
# that either is correct in isolation.
with contextlib.redirect_stderr(io.StringIO()):
    execSource(
        "from videocode import *\n\ns = Square(side=1)\n"
        "s.over(duration=0.5).fillColor = RED_B\ns.over(duration=0.5).strokeColor = BLUE_C\nwait(2)\n",
        "contention_test_channel.py",
    )
stored = {k for f, e in Context.stack[0].items() if f != -1 for k in e}
claimed = {c for st in Context.statements for c in st["keys"]}
check("stored keys and claimed channels agree on the args attributes",
      {k for k in stored if k.startswith("Args:")} == {c for c in claimed if c.startswith("Args:")})
check("and there are two of them, not one",
      len({k for k in stored if k.startswith("Args:")}) == 2)

# ---------------------------------------------------------------------------
summary()
