#!/usr/bin/env python3

"""
Assertion-based tests for effects batch 2:
- slideIn / slideOut / spinIn / zoomPunch / blurIn / flash / jelly templates
- duotone / vhs / zoomBlur fragment-shader Python bindings
Run directly: `python3 test/effects2_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.template.effect.other.blurIn import blurIn
from videocode.template.effect.other.flash import flash
from videocode.template.effect.other.jelly import jelly
from videocode.template.effect.other.slide import slideIn, slideOut
from videocode.template.effect.other.spinIn import spinIn
from videocode.template.effect.other.zoomPunch import zoomPunch


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


# ---------------------------------------------------------------------------
section("slideIn — enters offset, lands on destination")

r = Rectangle(width=1, height=1).position(2.0, 1.0)
r.apply(slideIn(direction=Direction.LEFT, distance=1.5, duration=0.5))
pos = framesWith(r.meta.index, "Position")
first, last = pos[min(pos)]["args"], pos[max(pos)]["args"]
check("starts 1.5 left of destination", abs(first["x"] - 0.5) < 0.05 and first["y"] == 1.0)
check("lands exactly on destination", last["x"] == 2.0 and last["y"] == 1.0)
ops = framesWith(r.meta.index, "Opacity")
check("fades in to 255", ops[max(ops)]["args"]["opacity"] == 255)

# ---------------------------------------------------------------------------
section("slideOut — exits toward direction, ends hidden")

r2 = Rectangle(width=1, height=1).position(0.0, 0.0)
r2.apply(slideOut(direction=Direction.RIGHT, distance=2.0, duration=0.5))
pos = framesWith(r2.meta.index, "Position")
check("travels the full distance", abs(pos[max(pos)]["args"]["x"] - 2.0) < 1e-6)
hides = framesWith(r2.meta.index, "Hide")
check("ends hidden", len(hides) == 1 and max(hides) >= max(pos))

# ---------------------------------------------------------------------------
section("spinIn — full rotation into place")

s = Rectangle(width=1, height=1)
s.apply(spinIn(rotations=1, duration=0.6))
rots = framesWith(s.meta.index, "Rotation")
degs = [e["args"]["degree"] for _, e in sorted(rots.items())]
check("starts a full turn back", abs(degs[0] + 360.0) < 5.0)
check("ends at 0", abs(degs[-1]) < 1e-6)
scales = framesWith(s.meta.index, "Scale")
check("scale settles at 1", abs(scales[max(scales)]["args"]["x"] - 1.0) < 1e-6)

# ---------------------------------------------------------------------------
section("zoomPunch — snaps up, settles back with a dip")

z = Rectangle(width=1, height=1)
z.apply(zoomPunch(scale=1.35, duration=0.5))
scales = framesWith(z.meta.index, "Scale")
xs = [e["args"]["x"] for _, e in sorted(scales.items())]
check("peaks near 1.35x", abs(max(xs) - 1.35) < 0.02)
check("ends exactly at 1", abs(xs[-1] - 1.0) < 1e-6)
peak = xs.index(max(xs))
check("dips below 1 after the peak (Back overshoot)", min(xs[peak:]) < 0.995)

# ---------------------------------------------------------------------------
section("blurIn — odd strengths resolving to sharp")

b = Rectangle(width=1, height=1)
b.apply(blurIn(strength=21, duration=0.6))
blurs = framesWith(b.meta.index, "Blur")
strengths = [e["args"]["strength"] for _, e in sorted(blurs.items())]
check("all strengths odd", all(v % 2 == 1 for v in strengths))
check("starts near full strength", strengths[0] >= 19)
check("monotonically resolves", all(a >= c for a, c in zip(strengths, strengths[1:])))
ops = framesWith(b.meta.index, "Opacity")
check("fades in to 255", ops[max(ops)]["args"]["opacity"] == 255)

# ---------------------------------------------------------------------------
section("flash — brightness pulse, nothing left at the end")

f = Rectangle(width=1, height=1)
f.apply(flash(amount=160, duration=0.4))
brs = framesWith(f.meta.index, "Brightness")
amounts = [e["args"]["amount"] for _, e in sorted(brs.items())]
check("peaks near 160", max(amounts) > 140)
check("returns toward 0", amounts[-1] < 30)

# ---------------------------------------------------------------------------
section("jelly — opposite-phase squash & stretch, exact restore")

j = Rectangle(width=1, height=1)
j.apply(jelly(amplitude=0.2, duration=0.6))
scales = framesWith(j.meta.index, "Scale")
pairs = [(e["args"]["x"], e["args"]["y"]) for _, e in sorted(scales.items())]
check("x and y move in opposite phase", any(x > 1.01 and y < 0.99 for x, y in pairs))
check("ends exactly at (1, 1)", pairs[-1] == (1.0, 1.0))

# ---------------------------------------------------------------------------
section("fragment shader bindings")

d = duotone(dark=BLUE_C, light=YELLOW)
check("duotone flattens colors to 0..1 floats", 0.0 <= d.darkR <= 1.0 and 0.0 <= d.lightB <= 1.0)
v = vhs(intensity=0.8)
check("vhs args", v.intensity == 0.8)
zb = zoomBlur(0.12)
check("zoomBlur args", zb.strength == 0.12)

t = Rectangle(width=1, height=1)
t.apply(duotone(), duration=0.2)
t.apply(vhs(), start=0.3, duration=0.2)
t.apply(zoomBlur(), start=0.6, duration=0.2)
names = {k for fr, e in Context.stack[t.meta.index].items() if fr != -1 for k in e}
check("Duotone lands in the stack", "Duotone" in names)
check("Vhs lands in the stack", "Vhs" in names)
check("ZoomBlur lands in the stack", "ZoomBlur" in names)

# ---------------------------------------------------------------------------
summary()
