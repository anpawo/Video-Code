#!/usr/bin/env python3

"""
Assertion-based smoke tests for `highlight()`
— `videocode/template/effect/other/highlight.py`. Briefly scales a `Polygon` up by
`scaleFactor` and flashes its `fillColor`, both via `Easing.ThereAndBack`
(`self(0) == self(1) == 0`) so the shape returns to its original size/color.
Run directly: `python3 test/highlight_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Rectangle, Context, Easing, YELLOW, RED
from videocode.template.effect.other.highlight import highlight

def approx(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) < tol

def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}

# ── default: scale pulse + YELLOW flash ─────────────────────────────────────
section("highlight(): default scaleFactor + YELLOW fillColor flash")
r = Rectangle(fillColor=RED)
r.apply(highlight(duration=0.2))

scaleFrames = framesWith(r.meta.index, "Scale")
check("Scale frames pushed", len(scaleFrames) > 1)

lastFrame = max(scaleFrames)
# Frame 0 is skipped (autodestroy: eased value at i=0 equals src, a no-op).
check("scale returns near 1.0", approx(scaleFrames[lastFrame]["args"]["x"], 1.0, tol=1e-2))

midFrame = sorted(scaleFrames)[len(scaleFrames) // 2]
check("scale peaks above 1.0 mid-animation", scaleFrames[midFrame]["args"]["x"] > 1.05)

colorFrames = framesWith(r.meta.index, "Args:fillColor")
check("Args:fillColor frames pushed", len(colorFrames) > 1)

lastColor = colorFrames[max(colorFrames)]["args"]["value"]
check("fillColor returns near RED", approx(lastColor.r, RED.r, tol=2) and approx(lastColor.g, RED.g, tol=2))

midColor = colorFrames[sorted(colorFrames)[len(colorFrames) // 2]]["args"]["value"]
firstColor = colorFrames[min(colorFrames)]["args"]["value"]
check("fillColor flashes toward YELLOW mid-animation", midColor.g > firstColor.g)

# ── color=None: scale-only, no fillColor frames ─────────────────────────────
section("highlight(color=None): scale-only, no fillColor frames")
r2 = Rectangle(fillColor=RED)
r2.apply(highlight(color=None, duration=0.2))

check("Scale frames pushed", len(framesWith(r2.meta.index, "Scale")) > 1)
check("no Args:fillColor frames", len(framesWith(r2.meta.index, "Args:fillColor")) == 0)

# ── custom scaleFactor + easing ──────────────────────────────────────────────
section("highlight(scale=1.5, color=None, easing=Easing.Wiggle)")
r3 = Rectangle(fillColor=RED)
r3.apply(highlight(scale=1.5, color=None, easing=Easing.Wiggle, duration=0.2))

wiggleFrames = framesWith(r3.meta.index, "Scale")
check("Scale frames pushed", len(wiggleFrames) > 1)
last = wiggleFrames[max(wiggleFrames)]["args"]["x"]
check("scale returns near 1.0 (wiggle)", approx(last, 1.0, tol=1e-2))

# ── summary ──────────────────────────────────────────────────────────────────
summary()
