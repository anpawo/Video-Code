#!/usr/bin/env python3

"""
Assertion-based tests for effects batch 6 (everyday explainer-video filters):
- roundCorners / feather / saturation / temperature / chromaticAberration /
  letterbox fragment-shader Python bindings
Run directly: `python3 test/effects6_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


# ---------------------------------------------------------------------------
section("fragment shader bindings")

check("roundCorners args", roundCorners(0.3).radius == 0.3)
check("feather args", feather(0.2).softness == 0.2)
check("saturation args", saturation(0.5).amount == 0.5)
check("temperature args", temperature(-0.4).warmth == -0.4)
check("chromaticAberration args", chromaticAberration(0.01).amount == 0.01)
check("letterbox args", letterbox(2.39).ratio == 2.39)

r = Rectangle(width=1, height=1)
r.apply(roundCorners(), duration=0.1)
r.apply(feather(), start=0.2, duration=0.1)
r.apply(saturation(), start=0.4, duration=0.1)
r.apply(temperature(), start=0.6, duration=0.1)
r.apply(chromaticAberration(), start=0.8, duration=0.1)
r.apply(letterbox(), start=1.0, duration=0.1)
names = {k for fr, e in Context.stack[r.meta.index].items() if fr != -1 for k in e}
for n in ("RoundCorners", "Feather", "Saturation", "Temperature", "ChromaticAberration", "Letterbox"):
    check(f"{n} lands in the stack", n in names)

# ---------------------------------------------------------------------------
summary()
