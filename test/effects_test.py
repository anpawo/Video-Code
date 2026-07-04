#!/usr/bin/env python3

"""
Assertion-based tests for the editor-style effects pack:
- Easing.Back / Elastic / Bounce rate functions
- typewriter / shake / popIn / pulse / wipeIn / wipeOut / kenBurns templates
- vignette / pixelate / glitch fragment-shader Python bindings
Run directly: `python3 test/effects_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.template.effect.other.kenBurns import kenBurns
from videocode.template.effect.other.popIn import popIn
from videocode.template.effect.other.pulse import pulse
from videocode.template.effect.other.shake import shake
from videocode.template.effect.other.typewriter import typewriter
from videocode.template.effect.other.wipe import wipeIn, wipeOut


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


# ---------------------------------------------------------------------------
section("Easing.Back / Elastic / Bounce")

for name in ("Back", "Elastic", "Bounce"):
    e = getattr(Easing, name)
    check(f"{name}(0) == 0", abs(e(0.0)) < 1e-9)
    check(f"{name}(1) == 1", abs(e(1.0) - 1.0) < 1e-9)
check("Back overshoots past 1", max(Easing.Back(t / 100) for t in range(101)) > 1.05)
check("Elastic overshoots past 1", max(Easing.Elastic(t / 100) for t in range(101)) > 1.05)
check("Bounce stays within [0, 1]", all(0.0 <= Easing.Bounce(t / 100) <= 1.0 + 1e-9 for t in range(101)))

# ---------------------------------------------------------------------------
section("typewriter — staggered letter reveal")

txt = Text("abc", fontSize=0.5)
txt.apply(typewriter(interval=0.1))
letterIdx = [l.meta.index for l in txt.inputs]
revealFrames = []
for idx in letterIdx:
    ops = framesWith(idx, "Opacity")
    on = [f for f, e in ops.items() if e["args"]["opacity"] == 255]
    check(f"letter #{idx} has a reveal frame", len(on) >= 1)
    revealFrames.append(min(on) if on else -1)
check("letters reveal in order, 0.1s apart", revealFrames == sorted(revealFrames) and len(set(revealFrames)) == 3)

# ---------------------------------------------------------------------------
section("shake — returns exactly to origin")

r = Rectangle(width=1, height=1).position(2.0, 1.0)
r.apply(shake(amplitude=0.5, duration=0.5))
pos = framesWith(r.meta.index, "Position")
last = pos[max(pos)]["args"]
check("shake emitted per-frame positions", len(pos) >= 10)
check("final frame back at origin", last["x"] == 2.0 and last["y"] == 1.0)
moved = any(e["args"]["x"] != 2.0 for e in pos.values())
check("intermediate frames displaced", moved)

# ---------------------------------------------------------------------------
section("popIn — scale overshoots then settles at original")

p = Rectangle(width=1, height=1)
p.apply(popIn(duration=0.5))
scales = framesWith(p.meta.index, "Scale")
xs = [e["args"]["x"] for _, e in sorted(scales.items())]
check("starts at 0.5x", abs(xs[0] - 0.5) < 0.02)
check("overshoots past 1", max(xs) > 1.01)
check("settles at 1", abs(xs[-1] - 1.0) < 1e-6)
ops = framesWith(p.meta.index, "Opacity")
check("fades in to 255", ops[max(ops)]["args"]["opacity"] == 255)

# ---------------------------------------------------------------------------
section("pulse — there and back")

c = Circle(radius=0.5)
c.apply(pulse(scale=1.2, duration=0.6))
scales = framesWith(c.meta.index, "Scale")
xs = [e["args"]["x"] for _, e in sorted(scales.items())]
check("peaks near 1.2x", abs(max(xs) - 1.2) < 0.02)
check("ends back at 1", abs(xs[-1] - 1.0) < 0.02)

# ---------------------------------------------------------------------------
section("wipeIn / wipeOut — crop sweep + persistence")

w1 = Rectangle(width=2, height=1)
w1.apply(wipeIn(direction="left", duration=0.5))
crops = framesWith(w1.meta.index, "Crop")
rs = [e["args"]["right"] for _, e in sorted(crops.items())]
check("wipeIn animates right crop 100 -> 0", abs(rs[0] - 100) < 1e-6 and abs(rs[-1]) < 1e-6)

w2 = Rectangle(width=2, height=1)
w2.apply(wipeOut(direction="right", duration=0.5))
crops = framesWith(w2.meta.index, "Crop")
ls = [e["args"]["left"] for _, e in sorted(crops.items())]
check("wipeOut animates left crop 0 -> 100", abs(ls[0]) < 1e-6 and abs(ls[-1] - 100) < 1e-6)
hides = framesWith(w2.meta.index, "Hide")
check("wipeOut ends hidden", len(hides) == 1 and max(hides) >= max(crops))

# ---------------------------------------------------------------------------
section("kenBurns — simultaneous zoom + pan")

k = Rectangle(width=2, height=1).position(0.0, 0.0)
k.apply(kenBurns(zoom=1.5, panX=0.4, panY=-0.2, duration=1.0))
scales = framesWith(k.meta.index, "Scale")
pos = framesWith(k.meta.index, "Position")
check("zooms to 1.5x", abs(scales[max(scales)]["args"]["x"] - 1.5) < 1e-6)
check("pans to (0.4, -0.2)", abs(pos[max(pos)]["args"]["x"] - 0.4) < 1e-6 and abs(pos[max(pos)]["args"]["y"] + 0.2) < 1e-6)
check("zoom and pan share frames", set(scales) == set(pos))

# ---------------------------------------------------------------------------
section("fragment shader bindings")

v = vignette(intensity=0.7, radius=40, smoothness=30)
check("vignette args", v.intensity == 0.7 and v.radius == 40 and v.smoothness == 30)
px = pixelate(24)
check("pixelate args", px.size == 24)
g1, g2 = glitch(), glitch()
check("glitch auto-seeds differ", g1.seed != g2.seed)
g3 = glitch(seed=7)
check("glitch explicit seed", g3.seed == 7)

s = Rectangle(width=1, height=1)
s.apply(vignette(), duration=0.2)
s.apply(glitch(seed=1), start=0.5, duration=0.2)
stacked = Context.stack[s.meta.index]
names = {k for f, e in stacked.items() if f != -1 for k in e}
check("Vignette lands in the stack", "Vignette" in names)
check("Glitch lands in the stack", "Glitch" in names)

# ---------------------------------------------------------------------------
summary()
