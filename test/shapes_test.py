#!/usr/bin/env python3

"""
Assertion-based smoke tests for shape geometry (#63) — Polygon/Rectangle/
Square/Triangle/EquilateralTriangle/RightTriangle/Circle/Curve: vertex
generation, buildPoints (corner rounding incl. sharpCorners and open paths),
prop-driven point regeneration (width/height/radius/cornerRadius), and
Polygon.contains.
Run directly: `python3 test/shapes_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Rectangle, Square, Circle, Triangle, EquilateralTriangle, RightTriangle, Curve, Context

def approx(a: float, b: float, eps: float = 1e-6) -> bool:
    return abs(a - b) <= eps

def pointsPushed(index: int) -> bool:
    return any("Args:points" in entry for f, entry in Context.stack[index].items() if f != -1)

# ── Rectangle: vertices, width/height, point count ───────────────────────────
section("Rectangle — vertices, width/height, buildPoints fast path")
r = Rectangle(width=4, height=2)

check("vertices form a 4x2 box", r.vertices == [(0, 0), (4, 0), (4, 2), (0, 2)])
check("width matches constructor", r.width == 4)
check("height matches constructor", r.height == 2)
check("points: 4 corners * 4 = 16 (cornerRadius=0)", len(r.points) == 16)
# fast path: each corner -> [v, v, v, mid(v, next)]
check("first corner has no rounding (arcStart == vertex == arcEnd)", r.points[0] == r.points[1] == r.points[2])

# ── Square ────────────────────────────────────────────────────────────────
section("Square — width == height == side")
sq = Square(side=3)
check("square width == side", sq.width == 3)
check("square height == side", sq.height == 3)

# ── Triangle / EquilateralTriangle / RightTriangle ──────────────────────────
section("Triangle — vertices from p0/p1/p2, Polygon.width/height")
t = Triangle(p0=(0, 0), p1=(2, 0), p2=(3, 2))
check("vertices == [p0, p1, p2]", t.vertices == [(0, 0), (2, 0), (3, 2)])
check("width == max-min x (3)", t.width == 3)
check("height == max-min y (2)", t.height == 2)

section("EquilateralTriangle — side-derived vertices")
import math

eq = EquilateralTriangle(side=2)
h = 2 * math.sqrt(3) / 2
check("vertices match equilateral formula", eq.vertices == [(0, 0), (2, 0), (1, h)])

section("RightTriangle — width/height-derived vertices")
rt = RightTriangle(width=4, height=3)
check("vertices == [(0,0), (w,0), (0,h)]", rt.vertices == [(0, 0), (4, 0), (0, 3)])

# ── Circle ───────────────────────────────────────────────────────────────────
section("Circle — raw contour, single contour (no contourSizes)")
c = Circle(radius=1)
check("32 control points (N=16 anchor+handle pairs)", len(c.points) == 32)
check("single contour -> contourSizes == []", c.contourSizes == [])

beforeRadiusPoints = list(c.points)
c.radius = 2
check("radius prop regenerates points", c.points != beforeRadiusPoints)
check("radius prop updated", c.radius == 2)
check("Args:points pushed after radius change", pointsPushed(c.meta.index))

# ── Curve (open polygon) ─────────────────────────────────────────────────────
section("Curve — open path point count (2n for n input points)")
curve = Curve(points=[(0, 0), (1, 0), (1, 1)])
check("open flag set", curve.open is True)
check("no fill contours -> contourSizes == []", curve.contourSizes == [])
check("open path emits 2n points", len(curve.points) == 6)
# cornerRadius=0 -> [v0, mid(v0,v1), v1, mid(v1,v2), v2, v2] in reversed-vertex order
rev = list(reversed(curve.vertices))
expectedMid01 = ((rev[0][0] + rev[1][0]) / 2, (rev[0][1] + rev[1][1]) / 2)
check("first anchor is last vertex (reversed order)", curve.points[0] == rev[0])
check("midpoint between first two reversed vertices", curve.points[1] == expectedMid01)
check("terminal anchor duplicated (dummy handle)", curve.points[-1] == curve.points[-2] == rev[-1])

# ── cornerRadius prop triggers updatePoints + Args:points ────────────────────
section("cornerRadius — prop change regenerates points and pushes Args:points")
r2 = Rectangle(width=4, height=4)
beforeCorner = list(r2.points)
r2.cornerRadius = 50
check("cornerRadius changes points", r2.points != beforeCorner)
check("rounded corner is no longer a single point", r2.points[0] != r2.points[1])
check("Args:points pushed after cornerRadius change", pointsPushed(r2.meta.index))

# ── width prop triggers vertex + point regeneration ───────────────────────────
section("width — prop change regenerates vertices and points")
r3 = Rectangle(width=2, height=2)
r3.width = 6
check("width setter regenerates vertices", r3.vertices == [(0, 0), (6, 0), (6, 2), (0, 2)])
check("width prop updated", r3.width == 6)
check("Args:points pushed after width change", pointsPushed(r3.meta.index))

# ── sharpCorners excludes a vertex from rounding ──────────────────────────────
section("sharpCorners — excluded vertex keeps a sharp corner despite cornerRadius")
r4 = Rectangle(width=4, height=4, cornerRadius=50)
# rev = reversed(vertices); buildPoints checks (n-1-i) in sharpCorners for rev index i.
# rev[0] == original vertex 3 == (0, 4); (n-1-0) == 3 -> sharpCorners={3} targets it.
r4.sharpCorners = {3}
r4.updatePoints()
check("corner 0 (sharp) has arcStart == vertex == arcEnd", r4.points[0] == r4.points[1] == r4.points[2])
check("corner 1 (rounded) is still rounded", r4.points[4] != r4.points[5])

# ── Polygon.contains ───────────────────────────────────────────────────────
section("Polygon.contains — point-in-polygon hit test")
r5 = Rectangle(width=4, height=2)  # local bbox: x in [0,4], y in [0,2]; default align=(0.5,0.5) -> pivot (2,1)
check("center of the rectangle is contained", r5.contains(0, 0))
check("far-away point is not contained", not r5.contains(100, 100))

# ── summary ────────────────────────────────────────────────────────────────
summary()
