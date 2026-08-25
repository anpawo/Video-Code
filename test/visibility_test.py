#!/usr/bin/env python3

"""
Assertion-based tests for visibility as a STATE: hidden or shown at a frame,
whatever order the two statements were typed in.
Run directly: `python3 test/visibility_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Context
from videocode.serialize import execSource


def visibility(line: str) -> dict[int, list[str]]:
    """Every visibility key the square is given, by frame, in the order C++ replays them."""
    execSource("from videocode import *\n\ns = Square(side=1)\nwait(0.5)\n" + line + "\nwait(1)\n", "visibility_test_scene.py")
    return {
        f: [key for key in entry if key in ("Hide", "Show")]
        for f, entry in Context.stack[0].items()
        if f != -1 and any(key in ("Hide", "Show") for key in entry)
    }


def hiddenAt(track: dict[int, list[str]], frame: int) -> bool:
    before = [f for f in track if f <= frame]
    # C++ replays a frame's keys in insertion order, so the last one holds.
    return bool(before) and track[max(before)][-1] == "Hide"


# ── Time decides, not the order the lines were typed in ─────────────────────
# The bug this guards: `autodestroy` asks whether a shader changes anything,
# and answers from the WRITE CURSOR. A `show()` written while the input was
# still visible was dropped as a no-op — correctly, at that instant — and then
# a `hide()` on a LATER line but an EARLIER frame hid it for the rest of the
# scene, with nothing left to turn it back on.
section("Visibility — the last statement in TIME wins, not the last typed")

inTimeOrder = visibility("s.apply(hide(), start=1)\ns.apply(show(), start=2)")
reversed_ = visibility("s.apply(show(), start=2)\ns.apply(hide(), start=1)")

check("written in time order: hidden at 1s, shown again at 2s", inTimeOrder == reversed_ and len(inTimeOrder) == 2)
check("hidden between the two", hiddenAt(reversed_, 60))
check("shown again after the second", not hiddenAt(reversed_, 90))
check("still hidden just before it", hiddenAt(reversed_, 74))

# ── One state, one entry per frame ──────────────────────────────────────────
# `Hide` and `Show` are two stack keys for one piece of state, and C++ replays
# a frame's keys in the dict's INSERTION order — so both landing on the same
# frame let the order the two calls were typed in decide which held, silently.
section("Visibility — a frame carries one of the two, never both")

hideThenShow = visibility("s.apply(hide(), start=1)\ns.apply(show(), start=1)")
showThenHide = visibility("s.apply(show(), start=1)\ns.apply(hide(), start=1)")

check("hide then show, one frame: a single key", hideThenShow == {45: ["Show"]})
check("show then hide, one frame: a single key", showThenHide == {45: ["Hide"]})
check("hide then show ends up shown", not hiddenAt(hideThenShow, 45))
check("show then hide ends up hidden", hiddenAt(showThenHide, 45))

# ---------------------------------------------------------------------------
summary()
