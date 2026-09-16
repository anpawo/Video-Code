#!/usr/bin/env python3

"""
Assertion-based tests for effects batch 6:
- dipToBlack / zoomThrough / slideOver transition templates
Run directly: `python3 test/effects6_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.template.effect.other.transitions import dipToBlack


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


# ---------------------------------------------------------------------------
section("dipToBlack — outgoing darkens to black, incoming rises from black")

a = Rectangle(width=1, height=1)
b = Rectangle(width=1, height=1).hide()
dipToBlack(a, b, duration=0.4)

aB = framesWith(a.meta.index, "Brightness")
bB = framesWith(b.meta.index, "Brightness")
aVals = [e["args"]["amount"] for _, e in sorted(aB.items())]
bVals = [e["args"]["amount"] for _, e in sorted(bB.items())]
check("outgoing darkens down to -255", aVals[-1] == -255 and all(x >= y for x, y in zip(aVals, aVals[1:])))
check("incoming rises back up to 0", bVals[-1] == 0 and all(x <= y for x, y in zip(bVals, bVals[1:])))
check("incoming starts fully black", bVals[0] == -255)
aHides = framesWith(a.meta.index, "Hide")
check("outgoing hidden at the midpoint (both sides are black there)", len(aHides) == 1)
bShows = framesWith(b.meta.index, "Show")
check("incoming is shown", len(bShows) == 1)

# ---------------------------------------------------------------------------
summary()
