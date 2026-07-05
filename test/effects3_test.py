#!/usr/bin/env python3

"""
Assertion-based tests for effects batch 3:
- bounceIn / swing / tada / stamp templates
- sepia / invert / posterize / hueRotate / halftone fragment-shader bindings
Run directly: `python3 test/effects3_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.template.effect.other.bounceIn import bounceIn
from videocode.template.effect.other.stamp import stamp
from videocode.template.effect.other.swing import swing
from videocode.template.effect.other.tada import tada


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


# ---------------------------------------------------------------------------
section("bounceIn — drops from above, lands exactly")

b = Rectangle(width=1, height=1).position(1.0, -2.0)
b.apply(bounceIn(height=2.0, duration=0.8))
pos = framesWith(b.meta.index, "Position")
first, last = pos[min(pos)]["args"], pos[max(pos)]["args"]
check("starts `height` above the landing spot", abs(first["y"] - 0.0) < 0.05 and first["x"] == 1.0)
check("lands exactly", last["x"] == 1.0 and last["y"] == -2.0)
ys = [e["args"]["y"] for _, e in sorted(pos.items())]
descents = sum(1 for a, c in zip(ys, ys[1:]) if c > a + 1e-9)
check("bounces back up at least once", descents >= 2)

# ---------------------------------------------------------------------------
section("swing — decaying oscillation, exact rest")

s = Rectangle(width=1, height=1)
s.apply(swing(angle=15, duration=1.0))
rots = framesWith(s.meta.index, "Rotation")
degs = [e["args"]["degree"] for _, e in sorted(rots.items())]
check("deflects both ways", max(degs) > 5 and min(degs) < -5)
check("ends exactly at rest", degs[-1] == 0.0)
check("decays (late peaks smaller)", max(abs(d) for d in degs[-8:-1]) < max(abs(d) for d in degs))

# ---------------------------------------------------------------------------
section("tada — shrink, enlarged shimmy, settle")

t = Rectangle(width=1, height=1)
t.apply(tada(duration=1.0))
scales = framesWith(t.meta.index, "Scale")
xs = [e["args"]["x"] for _, e in sorted(scales.items())]
rots = framesWith(t.meta.index, "Rotation")
degs = [e["args"]["degree"] for _, e in sorted(rots.items())]
check("dips to 0.9x", min(xs) < 0.92)
check("shimmies at 1.1x", max(xs) > 1.08)
check("wobbles both ways", max(degs) > 2 and min(degs) < -2)
check("settles at 1x / 0 deg", abs(xs[-1] - 1.0) < 1e-6 and abs(degs[-1]) < 1e-6)

# ---------------------------------------------------------------------------
section("stamp — slams from huge, impact ripple, exact rest")

st = Rectangle(width=1, height=1)
st.apply(stamp(scale=2.5, duration=0.6))
scales = framesWith(st.meta.index, "Scale")
xs = [e["args"]["x"] for _, e in sorted(scales.items())]
check("starts near 2.5x", xs[0] > 2.3)
check("ends exactly at 1", abs(xs[-1] - 1.0) < 1e-6)
ops = framesWith(st.meta.index, "Opacity")
check("fades in during the slam", ops[max(ops)]["args"]["opacity"] == 255)

# ---------------------------------------------------------------------------
section("fragment shader bindings")

check("sepia args", sepia(0.8).amount == 0.8)
check("invert args", invert().amount == 1.0)
check("posterize args", posterize(6).levels == 6)
check("hueRotate args", hueRotate(120).degrees == 120)
check("halftone args", halftone(14).size == 14)

r = Rectangle(width=1, height=1)
r.apply(sepia(), duration=0.1)
r.apply(invert(), start=0.2, duration=0.1)
r.apply(posterize(4), start=0.4, duration=0.1)
r.apply(hueRotate(90), start=0.6, duration=0.1)
r.apply(halftone(), start=0.8, duration=0.1)
names = {k for fr, e in Context.stack[r.meta.index].items() if fr != -1 for k in e}
for n in ("Sepia", "Invert", "Posterize", "HueRotate", "Halftone"):
    check(f"{n} lands in the stack", n in names)

# ---------------------------------------------------------------------------
summary()
