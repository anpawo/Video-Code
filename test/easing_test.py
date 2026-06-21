#!/usr/bin/env python3

"""
Assertion-based smoke tests for the Manim-inspired rate functions added to
`Easing` (`videocode/utils/bezier.py`): `Smooth`, `RushInto`, `RushFrom`,
`SlowInto`, `DoubleSmooth`, `ThereAndBack`, `ThereAndBackWithPause`, `Wiggle`,
`ExponentialDecay`. These are `Func`-based `RateFunc`s (not `CubicBezier`),
exercising the generalized `easing` type used by `ease`/`moveTo`/`scaleTo`/
`rotateTo`/`fadeIn`/... .
Run directly: `python3 test/easing_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Rectangle, Context, Easing

def approx(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) < tol

# ── 0→1 rate functions ──────────────────────────────────────────────────────
section("0->1 rate functions: endpoints")
for name in ("Smooth", "RushInto", "RushFrom", "SlowInto", "DoubleSmooth"):
    f = getattr(Easing, name)
    check(f"{name}(0) == 0", approx(f(0), 0))
    check(f"{name}(1) == 1", approx(f(1), 1))

# ── "there and back" rate functions: start == end ───────────────────────────
section("there-and-back rate functions: start == end")
check("ThereAndBack(0) == 0", approx(Easing.ThereAndBack(0), 0))
check("ThereAndBack(1) == 0", approx(Easing.ThereAndBack(1), 0))
check("ThereAndBack(0.5) == 1 (peak)", approx(Easing.ThereAndBack(0.5), 1))

check("ThereAndBackWithPause(0) == 0", approx(Easing.ThereAndBackWithPause(0), 0))
check("ThereAndBackWithPause(1) == 0", approx(Easing.ThereAndBackWithPause(1), 0))
check("ThereAndBackWithPause(0.5) == 1 (plateau)", approx(Easing.ThereAndBackWithPause(0.5), 1))

check("Wiggle(0) == 0", approx(Easing.Wiggle(0), 0))
check("Wiggle(1) == 0", approx(Easing.Wiggle(1), 0))

# ── exponential decay ────────────────────────────────────────────────────────
section("ExponentialDecay")
check("ExponentialDecay(0) == 0", approx(Easing.ExponentialDecay(0), 0))
check("ExponentialDecay(1) ~= 1", approx(Easing.ExponentialDecay(1), 1, tol=1e-3))

# ── rangeIdx/range smoke test on a Func-based easing ────────────────────────
section("rangeIdx on a Func-based easing")
samples = list(Easing.Wiggle.rangeIdx(0, 10, 0.2))  # 6 frames
check("rangeIdx produced frames", len(samples) == 6)
check("first sample ~= start", approx(samples[0][0], 0))
check("last sample ~= start (wiggle returns)", approx(samples[-1][0], 0))

# ── end-to-end: Input.rotateBy/moveBy with the new easings ──────────────────
section("Input.rotateBy(easing=Easing.Wiggle) — wiggles out and back")
r = Rectangle()
r.rotateBy(30, easing=Easing.Wiggle, duration=0.2)  # 6 frames

rotFrames = sorted(f for f, entry in Context.stack[r.meta.index].items() if f != -1 and "Rotation" in entry)
check("Rotation frames pushed", len(rotFrames) > 1)
lastDegree = Context.stack[r.meta.index][rotFrames[-1]]["Rotation"]["args"]["degree"]
check("final rotation back near start (0)", approx(lastDegree, 0, tol=1e-2))
check("rotation meta updated", approx(r.meta.rotation, lastDegree))

section("Input.moveBy(easing=Easing.ThereAndBack) — moves out and back")
r2 = Rectangle()
r2.moveBy(x=2, easing=Easing.ThereAndBack, duration=0.2)  # 6 frames

posFrames = sorted(f for f, entry in Context.stack[r2.meta.index].items() if f != -1 and "Position" in entry)
check("Position frames pushed", len(posFrames) > 1)
lastX = Context.stack[r2.meta.index][posFrames[-1]]["Position"]["args"]["x"]
check("final x back near start (0)", approx(lastX, 0, tol=1e-2))

# ── summary ──────────────────────────────────────────────────────────────────
summary()
