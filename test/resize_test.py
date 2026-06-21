#!/usr/bin/env python3

"""
Assertion-based smoke tests for animating geometry-affecting properties
(width/height/radius) via `Input.ease` — #125 Phase 2 "animating width/height".
`width`/`height`/`radius` are `@prop(onSet=Polygon.updatePoints)`, so each
eased step rebuilds `points` and pushes a fresh `Args:points` shader — `ease`
(generic over any attribute) already produces a smooth, frame-by-frame
geometry animation with no new template code needed.
Run directly: `python3 test/resize_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Rectangle, Circle, Context

def pointsFrames(index: int) -> dict[int, list[tuple[float, float]]]:
    return {
        f: entry["Args:points"]["args"]["value"]
        for f, entry in Context.stack[index].items()
        if f != -1 and "Args:points" in entry
    }

def width(points: list[tuple[float, float]]) -> float:
    return max(p[0] for p in points) - min(p[0] for p in points)

# ── width animates from 2 to 6 over 6 frames ────────────────────────────────
section("ease('width', ...) — smooth per-frame geometry animation")
r = Rectangle(width=2, height=2)
r.ease("width", 6, duration=0.2)  # 6 frames

frames = pointsFrames(r.meta.index)
check("multiple Args:points frames pushed", len(frames) > 1)
widths = [width(frames[f]) for f in sorted(frames)]
check("width increases monotonically", all(b > a for a, b in zip(widths, widths[1:])))
check("final width matches target", widths[-1] == 6)
check("width prop updated", r.width == 6)

# ── radius animates from 0.5 to 2 over 6 frames ─────────────────────────────
section("ease('radius', ...) — same generic mechanism on Circle")
c = Circle(radius=0.5)
c.ease("radius", 2, duration=0.2)  # 6 frames

frames = pointsFrames(c.meta.index)
check("multiple Args:points frames pushed", len(frames) > 1)
widths = [width(frames[f]) for f in sorted(frames)]
check("circle diameter increases monotonically", all(b > a for a, b in zip(widths, widths[1:])))
check("final radius matches target", c.radius == 2)

# ── summary ──────────────────────────────────────────────────────────────────
summary()
