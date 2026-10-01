#!/usr/bin/env python3

"""
Assertion-based tests for the transitions taken from short-form edits:
- flash / whipPan / glitchCut / filmBurn
Run directly: `python3 test/transitions3_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.template.effect.other.transitions import filmBurn, flash, glitchCut, whipPan


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


def values(index: int, key: str, arg: str) -> list:
    return [e["args"][arg] for _, e in sorted(framesWith(index, key).items())]


# ---------------------------------------------------------------------------
section("flash — outgoing burns up to white, incoming comes down out of it")

a = Rectangle(width=1, height=1)
b = Rectangle(width=1, height=1).hide()
flash(a, b, duration=0.4)

aVals, bVals = values(a.meta.index, "Brightness", "amount"), values(b.meta.index, "Brightness", "amount")
check("outgoing brightens up to +255", aVals[-1] == 255 and all(x <= y for x, y in zip(aVals, aVals[1:])))
check("incoming starts fully white and comes down to 0", bVals[0] == 255 and bVals[-1] == 0)
check("the cut is at the white midpoint", len(framesWith(a.meta.index, "Hide")) == 1 and len(framesWith(b.meta.index, "Show")) == 1)
check("the cut frame is the one where the incoming is shown", min(framesWith(b.meta.index, "Show")) == min(framesWith(a.meta.index, "Hide")))

# ---------------------------------------------------------------------------
section("whipPan — a full-frame push, smeared by a blur that peaks at the cut")

o = Rectangle(width=1, height=1).position(0.0, 0.0)
i = Rectangle(width=1, height=1).position(0.0, 0.0).hide()
whipPan(o, i, direction=Direction.LEFT, duration=0.4)

oXs = values(o.meta.index, "Position", "x")
iXs = values(i.meta.index, "Position", "x")
check("outgoing leaves a whole frame to the left", abs(oXs[-1] + W) < 1e-6)
check("incoming enters from a frame to the right and lands at 0", abs(iXs[0] - W) < 1e-6 and abs(iXs[-1]) < 1e-6)
oBlur, iBlur = values(o.meta.index, "Blur", "strength"), values(i.meta.index, "Blur", "strength")
check("outgoing blur grows toward the cut", oBlur[-1] > oBlur[0])
check("incoming blur fades out to none (kernel 1)", iBlur[0] > 1 and iBlur[-1] == 1)
check("every blur kernel is odd", all(int(s) % 2 == 1 for s in oBlur + iBlur))

# ---------------------------------------------------------------------------
section("glitchCut — both sides tear, the cut lands in the tear")

g1 = Rectangle(width=1, height=1)
g2 = Rectangle(width=1, height=1).hide()
glitchCut(g1, g2, duration=0.4, seed=7)

check("outgoing glitches", len(framesWith(g1.meta.index, "Glitch")) > 0)
check("incoming glitches", len(framesWith(g2.meta.index, "Glitch")) > 0)
seeds = {e["args"]["seed"] for e in framesWith(g1.meta.index, "Glitch").values()} | {e["args"]["seed"] for e in framesWith(g2.meta.index, "Glitch").values()}
check(f"seeds are the fixed ones, not drawn (got {sorted(seeds)})", seeds <= {7, 8})
check("the cut is hard: one hide, one show", len(framesWith(g1.meta.index, "Hide")) == 1 and len(framesWith(g2.meta.index, "Show")) == 1)

# ---------------------------------------------------------------------------
section("filmBurn — a glow added over the frame hides the cut")

f1 = Rectangle(width=1, height=1)
f2 = Rectangle(width=1, height=1).hide()
glow = filmBurn(f1, f2, duration=0.8)

ops = values(glow.meta.index, "Opacity", "opacity")
check("the glow rises to full and falls back to nothing", max(ops) == 255.0 and ops[-1] == 0.0)
peak = [f for f, e in framesWith(glow.meta.index, "Opacity").items() if e["args"]["opacity"] == 255.0]
cut = min(framesWith(f2.meta.index, "Show"))
check(f"the cut (frame {cut}) sits under the glow's peak (frames {peak})", any(abs(cut - p) <= 1 for p in peak))
xs = values(glow.meta.index, "Position", "x")
check("the glow drifts left to right", xs[0] < 0 < xs[-1])

# ---------------------------------------------------------------------------
summary()
