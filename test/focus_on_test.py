#!/usr/bin/env python3

"""
Assertion-based smoke tests for `FocusOn`
(`videocode/template/input/FocusOn.py`) — Manim-inspired `FocusOn`: a
translucent circle that starts large and transparent, then shrinks onto a
point while fading in — a "spotlight converging on a point" attention cue.
Run directly: `python3 test/focus_on_test.py`
"""

import sys

sys.path.insert(0, ".")

from videocode import Context, GRAY, TRANSPARENT, RED
from videocode.template.input._inputs import FocusOn

failures: list[str] = []


def check(label: str, condition: bool):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


def approx(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) < tol


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


# ── default: starts large/transparent, shrinks + fades in onto the point ────
print("FocusOn(x, y): default styling, shrink + fade in")
f = FocusOn(1, 2)

check("positioned at (x, y)", approx(f.meta.position.x, 1) and approx(f.meta.position.y, 2))
check("starts at startRadius", approx(f.radius, 3))
check("strokeColor is transparent", f.strokeColor == TRANSPARENT)
check("default fillColor is GRAY at 20% alpha", f.fillColor.r == GRAY.r and approx(f.fillColor.a, 255 * 0.2, tol=1))

scaleFrames = framesWith(f.meta.index, "Scale")
opacityFrames = framesWith(f.meta.index, "Opacity")
check("Scale frames pushed (shrink)", len(scaleFrames) > 1)
check("Opacity frames pushed (fade in)", len(opacityFrames) > 1)

lastScale = scaleFrames[max(scaleFrames)]["args"]["x"]
check("final scale == endRadius/startRadius", approx(lastScale, 0.2 / 3))

lastOpacity = opacityFrames[max(opacityFrames)]["args"]["opacity"]
check("final opacity == 255 (fully applies fillColor's alpha)", approx(lastOpacity, 255))

firstOpacity = opacityFrames[min(opacityFrames)]["args"]["opacity"]
check("fades in from 0", firstOpacity < lastOpacity)


# ── custom radii/color/duration ──────────────────────────────────────────────
print("FocusOn(x, y, color=RED, startRadius=1, endRadius=0.5)")
f2 = FocusOn(0, 0, color=RED, startRadius=1, endRadius=0.5, duration=0.5)

check("custom fillColor", f2.fillColor.r == RED.r and f2.fillColor.g == RED.g)
scaleFrames2 = framesWith(f2.meta.index, "Scale")
lastScale2 = scaleFrames2[max(scaleFrames2)]["args"]["x"]
check("final scale == endRadius/startRadius (custom)", approx(lastScale2, 0.5))


# ── summary ──────────────────────────────────────────────────────────────────
print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All checks passed.")
