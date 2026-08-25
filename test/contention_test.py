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

fight = contentions("s.moveTo(x=2, duration=1)\ns.moveBy(y=1, duration=1)")
check("the pair is reported", len(fight) == 1)
check("named by key", fight and fight[0]["key"] == "Position")
check("both call sites are named", fight and {fight[0]["a"]["call"], fight[0]["b"]["call"]} == {"moveTo", "moveBy"})
check("with the frames they share", fight and fight[0]["frames"] == 30)

check(
    "reported whichever order the two lines are in",
    len(contentions("s.moveBy(y=1, duration=1)\ns.moveTo(x=2, duration=1)")) == 1,
)
check(
    "partial overlap counts too",
    len(contentions("s.moveTo(x=2, duration=1)\ns.moveBy(y=1, start=0.5, duration=1)")) == 1,
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
    not contentions("s.moveTo(x=2, duration=1)\ns.flush()\ns.moveBy(y=1, duration=1)"),
)
check(
    "back to back, sharing only the handover frame",
    not contentions("s.moveTo(x=2, duration=1)\ns.moveBy(y=1, start=1, duration=1)"),
)
check("one statement is never its own rival", not contentions("s.moveTo(x=2, duration=1)"))

# ---------------------------------------------------------------------------
summary()
