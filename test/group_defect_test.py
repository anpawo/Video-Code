#!/usr/bin/env python3

"""
The group defect, closed — and now asserted the other way round.

A group re-emitted an absolute two-axis `position()` to every member on every
frame of its window, so a member animating ITSELF over those same frames had
its animation overwritten: 29 frames out of 30, no error, no warning, a plain
leaf hit exactly as hard as a nested group. Item 4 of the redesign in
`docs/WORKFLOWS.md` composes the two timelines instead, and these checks are
what that means: the member keeps its own climb AND takes the group's move.

The file was written to fail the day the redesign landed, and it did. That was
the whole point of naming the defect here rather than pinning it in a golden —
a golden would have recorded the bug as a picture, which is how twenty-four of
them came to describe behaviour three commits had deliberately replaced.
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


section("a member's own animation composes with its group's (item 4, closed)")

ALONE = "a = Square(side=1).position(-1, 0)\na.moveBy(y=4, duration=1)"
UNDER = ALONE + "\nb = Square(side=1).position(1, 0)\nGroup(a, b).moveBy(x=6, duration=1)"

alone = positions(ALONE, 0)
under = positions(UNDER, 0)

check("on its own, the member climbs across its whole window",
      len({y for _, y in alone if y is not None}) > 20)
# The defect was that these collapsed to the handful of values the group's own
# emission carried. Composed, the climb survives the group untouched and the
# group's move arrives on the other axis.
check("under a group, the climb survives whole",
      len({y for _, y in under if y is not None}) == len({y for _, y in alone if y is not None}))
check("and the group's move arrives on top of it",
      under[-1] == (5.0, 4.0))
check("the group moved it on every frame it covered, not just at the end",
      len({x for x, _ in under if x is not None}) > 20)

section("rotation composed all along — position has caught up")

# Rotation composed before position did, and that asymmetry was the shape of
# the defect: the same call, two answers. It stays asserted because it is the
# behaviour position has now been brought into line with.
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
