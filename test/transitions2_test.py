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
from videocode.template.effect.other.transitions import dipToBlack, slideOver, zoomThrough


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
section("zoomThrough — outgoing zooms up and out, incoming settles down from a zoom-in")

out = Rectangle(width=1, height=1)
inc = Rectangle(width=1, height=1).hide()
zoomThrough(out, inc, zoom=1.5, duration=0.4)

outScale = framesWith(out.meta.index, "Scale")
incScale = framesWith(inc.meta.index, "Scale")
outXs = [e["args"]["x"] for _, e in sorted(outScale.items())]
incXs = [e["args"]["x"] for _, e in sorted(incScale.items())]
check("outgoing scales up", outXs[-1] > outXs[0])
check("outgoing ends at 1.5x", abs(outXs[-1] - 1.5) < 1e-6)
check("incoming starts scaled up and settles to its resting scale", incXs[0] > incXs[-1] and abs(incXs[-1] - 1.0) < 1e-6)
outOps = framesWith(out.meta.index, "Opacity")
outOVals = [e["args"]["opacity"] for _, e in sorted(outOps.items())]
check("outgoing fades out", outOVals[-1] == 0.0 and all(x >= y for x, y in zip(outOVals, outOVals[1:])))
incShows = framesWith(inc.meta.index, "Show")
check("incoming is shown", len(incShows) == 1)

# ---------------------------------------------------------------------------
section("slideOver — incoming slides in, outgoing untouched")

o2 = Rectangle(width=1, height=1).position(0.0, 0.0)
i2 = Rectangle(width=1, height=1).position(0.0, 0.0).hide()
slideOver(o2, i2, direction=Direction.RIGHT, distance=2.0, duration=0.4)

check("outgoing has no position shader at all", len(framesWith(o2.meta.index, "Position")) == 0)
i2Pos = framesWith(i2.meta.index, "Position")
i2Xs = [e["args"]["x"] for _, e in sorted(i2Pos.items())]
check("incoming enters from the right, lands at 0", i2Xs[0] > 0.0 and abs(i2Xs[-1]) < 1e-6)
i2Shows = framesWith(i2.meta.index, "Show")
check("incoming is shown", len(i2Shows) == 1)

# ---------------------------------------------------------------------------
summary()
