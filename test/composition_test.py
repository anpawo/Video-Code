#!/usr/bin/env python3

"""
Assertion-based tests for composing effects whose windows do not line up.

Two effects on DIFFERENT channels must both survive, whatever their starts,
durations and ends. Two effects on the SAME channel still overwrite — that is
the accepted limit, and `contendedKeys()` is what makes it visible.
Run directly: `python3 test/composition_test.py`
"""

import contextlib
import io
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Context
from videocode.serialize import execSource


def resolve(body: str, index: int = 0) -> dict[int, tuple[float, float]]:
    """
    The position each frame actually renders at — the way C++ reads the stack.

    Not the same thing as the stack's own entries. `AInput::add` keeps ONE
    Metadata per frame and grows it by copying the last one, so a channel no
    entry claims holds the value it last had. Resolving here is what lets this
    file assert on the rendered trajectory without a rebuild — and it encodes
    the contract the C++ side owes: **frames replayed in increasing order**, a
    channel left unclaimed carried forward.
    """
    source = "from videocode import *\n\ns = Square(side=1).position(x=0, y=0)\n" + body + "\nwait(3)\n"
    with contextlib.redirect_stderr(io.StringIO()):
        execSource(source, "composition_test_scene.py")

    out: dict[int, tuple[float, float]] = {}
    x, y = 0.0, 0.0
    for frame in sorted(f for f in Context.stack[index] if f != -1):
        args = Context.stack[index][frame].get("Position")
        if args is not None:
            claimed = args["args"]
            x = claimed["x"] if claimed["x"] is not None else x
            y = claimed["y"] if claimed["y"] is not None else y
        out[frame] = (x, y)
    return out


def ramps(track: dict[int, tuple[float, float]], axis: int, first: int, last: int) -> bool:
    """
    The axis TRAVELS across those frames rather than jumping.

    Monotonicity alone would not catch the bug: a teleport is monotone too. What
    separates an animation from a snap is the size of a single step — an eased
    ramp spends its travel over every frame it covers, a snap spends it in one.
    """
    frames = [f for f in sorted(track) if first <= f <= last]
    values = [track[f][axis] for f in frames]
    if len(values) < 3:
        return False
    travel = values[-1] - values[0]
    if travel <= 0:
        return False
    steps = [b - a for a, b in zip(values, values[1:])]
    return all(step >= 0 for step in steps) and max(steps) < travel / 4


# ── Different channels must not destroy each other ─────────────────────────
# The bug this guards: `moveTo(x=2)` filled in the y it was never given, from
# the cursor, and `moveBy(y=3)` did the same for x — so whichever ran second
# wrote the first one's DESTINATION over every frame of its own window. With
# identical windows the x animation vanished entirely (2.00 from frame 1); with
# offset windows it played, then snapped to its endpoint the instant the y
# animation started writing.
section("Composition — two axes, one input, windows that do not line up")

sameWindow = resolve("s.moveTo(x=2, duration=1)\ns.moveBy(y=3, duration=1)")
check("x ramps instead of teleporting", ramps(sameWindow, 0, 1, 30))
check("y ramps too", ramps(sameWindow, 1, 1, 30))
check("both land where they were sent", sameWindow[max(sameWindow)] == (2.0, 3.0))

offset = resolve("s.moveTo(x=2, duration=1)\ns.moveBy(y=3, start=0.5, duration=2)")
check("x ramps over its own window", ramps(offset, 0, 1, 30))
check("x then HOLDS while y is still going", offset[45][0] == 2.0 and offset[60][0] == 2.0)
check("y is still ramping there", ramps(offset, 1, 20, 70))
check("both land where they were sent", offset[max(offset)] == (2.0, 3.0))

# ── The order the two lines were typed in must not matter ──────────────────
section("Composition — writing the two lines the other way round")

check(
    "same animation whichever line comes first",
    resolve("s.moveTo(x=2, duration=1)\ns.moveBy(y=3, start=0.5, duration=2)")
    == resolve("s.moveBy(y=3, start=0.5, duration=2)\ns.moveTo(x=2, duration=1)"),
)
check(
    "and when the SECOND line starts EARLIER than the first",
    resolve("s.moveTo(x=2, start=1, duration=1)\ns.moveBy(y=3, start=0, duration=0.5)")
    == resolve("s.moveBy(y=3, start=0, duration=0.5)\ns.moveTo(x=2, start=1, duration=1)"),
)

# ── The limit, stated ──────────────────────────────────────────────────────
# Two effects claiming the SAME channel still overwrite. That is wanted, not
# fixed: `contendedKeys()` is what makes it visible.
section("Composition — the same channel is still last-writer-wins")

sameAxis = resolve("s.moveTo(x=2, duration=1)\ns.moveTo(x=5, duration=1)")
check("the second one wins its channel", sameAxis[max(sameAxis)][0] == 5.0)
check("and the untouched axis is left alone", sameAxis[max(sameAxis)][1] == 0.0)

# ---------------------------------------------------------------------------
summary()
