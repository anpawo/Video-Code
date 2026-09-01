#!/usr/bin/env python3

"""
The group defect, named rather than pinned in a golden.

A group re-emits an absolute two-axis `position()` to every member on every
frame of its window. A member that was animating ITSELF over those same frames
has its animation overwritten — measured at 29 frames out of 30 — with no error
and no warning, and it happens to a plain leaf exactly as it happens to a
nested group. `docs/WORKFLOWS.md` records the redesign that closes it and why it
is deliberately postponed.

These checks assert what the code does TODAY. When the redesign lands they will
fail, and that failure is the point: it is the signal that the defect is gone,
and the moment to rewrite this file into the assertion of the fixed behaviour.
Recording it as a golden instead would have pinned the bug in a picture — which
is how twenty-four goldens came to describe behaviour that three commits had
deliberately replaced.
"""

import contextlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helpers import check, section, summary

from videocode.context import Context
from videocode.serialize import execSource


def positions(body: str, index: int) -> list[tuple]:
    """Every (x, y) the input at `index` is told to be, frame by frame."""
    with contextlib.redirect_stderr(io.StringIO()):
        execSource("from videocode import *\n\n" + body + "\nwait(2)\n", "group_defect_test.py")
    out = []
    for frame in sorted(f for f in Context.stack[index] if f != -1):
        entry = Context.stack[index][frame].get("Position")
        if entry:
            out.append((entry["args"].get("x"), entry["args"].get("y")))
    return out


section("a group overwrites a member's own POSITION animation (the open defect)")

ALONE = "a = Square(side=1).position(-1, 0)\na.moveBy(y=4, duration=1)"
UNDER = ALONE + "\nb = Square(side=1).position(1, 0)\nGroup(a, b).moveBy(x=6, duration=1)"

alone = positions(ALONE, 0)
under = positions(UNDER, 0)

check("on its own, the member climbs across its whole window",
      len({y for _, y in alone if y is not None}) > 20)
# The defect: under a group, those distinct y values collapse to the handful the
# group's own emission carries. If this check ever fails, the member kept its
# climb — the redesign landed, and this file should be rewritten.
check("under a group, that climb is gone (THIS FAILING IS GOOD NEWS)",
      len({y for _, y in under if y is not None}) < len({y for _, y in alone if y is not None}))

section("rotation survives, and that asymmetry is the shape of the defect")

# A group always writes `pos`; it writes `rot`/`scl` only when the author asked
# it to. So a member's rotation composes with a group's move, and its position
# does not — the same call, two answers.
ROT = "a = Square(side=1).position(-1, 0)\na.rotateBy(180, duration=1)\nb = Square(side=1).position(1, 0)\nGroup(a, b).moveBy(x=6, duration=1)"
with contextlib.redirect_stderr(io.StringIO()):
    execSource("from videocode import *\n\n" + ROT + "\nwait(2)\n", "g.py")
turns = {Context.stack[0][f]["Rotation"]["args"]["degree"] for f in Context.stack[0] if f != -1 and "Rotation" in Context.stack[0][f]}

check("the member's rotation survives the group's move", len(turns) > 20)
check("and reaches its full turn", max(turns) == 180)

section("a member appended after the group was built still moves (fixed 2026-09-01)")

APPEND = "a = Square(side=1).position(-1, 0)\nb = Square(side=1).position(1, 0)\ng = Group(a, b)\nc = Square(side=1).position(5, 0)\ng.inputs.append(c)\ng.moveBy(x=10, duration=1)"
appended = positions(APPEND, 2)
check("the appended member is carried like the others",
      bool(appended) and appended[-1][0] == 15.0)

summary()
