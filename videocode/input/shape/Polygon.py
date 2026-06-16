#!/usr/bin/env python3

from __future__ import annotations

import math

from abc import abstractmethod
from videocode.input.input import Input
from videocode.utils.classutils import Maybe
from videocode.utils.decorators import inputCreation, prop
from videocode.ty import *
from videocode.constants import *


class Polygon(Input):
    cppName = "Polygon"
    cppAttrs = {
        "points",
        "fillColor",
        "strokeColor",
        "strokeWidth",
        "open",
        "contourSizes",
    }

    @inputCreation
    def __init__(
        self,
        vertices: list[point],
        fillColor: rgba,
        strokeColor: rgba,
        strokeWidth: wufloat,
        cornerRadius: percent = 0,
        sharpCorners: set[int] = set(),
        open: bool = False,
    ):
        self.vertices = vertices
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth
        self.cornerRadius = cornerRadius
        self.sharpCorners = sharpCorners
        self.open = open
        self.points = self.buildPoints()

    @abstractmethod
    def generateVertices(self) -> list[point]: ...

    def generateRawContours(self) -> maybe[list[list[point]]]:
        """
        Subclass hook: per-contour anchor-handle control points used verbatim
        by buildPoints (no corner emission, no reversal). Multiple contours
        render as one shape — the first ring of each outer/holes group is
        filled with earcut holes and every contour is stroked separately
        (Letter glyphs, Circle). None = derive points from self.vertices.
        """
        return None

    def updatePoints(self):
        self.vertices = self.generateVertices()
        self.points = self.buildPoints()

    @prop(onSet=updatePoints)
    def cornerRadius() -> percent: ...

    @property
    def width(self) -> wunumber:
        xs = [v[0] for v in self.vertices]
        return max(xs) - min(xs)

    @property
    def height(self) -> wunumber:
        ys = [v[1] for v in self.vertices]
        return max(ys) - min(ys)

    def buildPoints(self) -> list[point]:
        """
        Build bezier control points (anchor-handle pairs) from self.vertices
        and self.cornerRadius.

        Iterates in reversed vertex order so C++ only needs to negate y (no reversal).

        Closed (default): each corner produces 4 points —
        arcStart, cornerHandle, arcEnd, connectorMidpoint — and the path wraps
        back to the first corner.

        Open: straight segments between consecutive vertices, interior corners
        rounded by cornerRadius, endpoints always sharp; the final anchor gets
        a dummy handle (C++ drops the wrap segment when open). No fill is drawn.
        """

        raw = self.generateRawContours()
        if raw is not None:
            self.contourSizes = [len(c) for c in raw] if len(raw) > 1 else []
            return [p for c in raw for p in c]
        self.contourSizes = []

        verts = self.vertices
        n = len(verts)
        if n < 2:
            return list(verts)

        frac = self.cornerRadius / 100.0
        rev = list(reversed(verts))

        if self.open:
            return self._buildOpenPoints(rev, frac)

        # Fast path: no rounded corners — skip all dist/unit work.
        # Output is identical to the general path with r=0 everywhere:
        # each corner emits [v, v, v, mid(v, next_v)].
        if frac == 0:
            bezier = []
            for i in range(n):
                nxt = (i + 1) % n
                bezier.append(rev[i])
                bezier.append(rev[i])
                bezier.append(rev[i])
                bezier.append(((rev[i][0] + rev[nxt][0]) / 2, (rev[i][1] + rev[nxt][1]) / 2))
            return bezier

        def dist(a, b):
            return math.hypot(b[0] - a[0], b[1] - a[1])

        def unit(a, b):
            d = dist(a, b)
            return ((b[0] - a[0]) / d, (b[1] - a[1]) / d) if d > 1e-9 else (0.0, 0.0)

        arcStart = []
        arcEnd = []
        for i in range(n):
            prev = (i - 1 + n) % n
            nxt = (i + 1) % n
            maxR = min(dist(rev[i], rev[prev]), dist(rev[i], rev[nxt])) * 0.5
            r = 0 if (n - 1 - i) in self.sharpCorners else frac * maxR
            uIn = unit(rev[i], rev[prev])
            uOut = unit(rev[i], rev[nxt])
            arcStart.append((rev[i][0] + uIn[0] * r, rev[i][1] + uIn[1] * r))
            arcEnd.append((rev[i][0] + uOut[0] * r, rev[i][1] + uOut[1] * r))

        bezier = []
        for i in range(n):
            nxt = (i + 1) % n
            mid = ((arcEnd[i][0] + arcStart[nxt][0]) / 2, (arcEnd[i][1] + arcStart[nxt][1]) / 2)
            bezier.append(arcStart[i])
            bezier.append(rev[i])
            bezier.append(arcEnd[i])
            bezier.append(mid)
        return bezier

    def _buildOpenPoints(self, rev: list[point], frac: float) -> list[point]:
        """
        Anchor-handle pairs for an open path: a quadratic corner curve per
        rounded interior vertex (endpoints stay sharp) and a straight segment
        curve between vertices. With cornerRadius=0 this emits exactly
        [v0, mid01, v1, mid12, ..., vLast, vLast] — one curve per segment.
        """

        n = len(rev)

        def dist(a, b):
            return math.hypot(b[0] - a[0], b[1] - a[1])

        def unit(a, b):
            d = dist(a, b)
            return ((b[0] - a[0]) / d, (b[1] - a[1]) / d) if d > 1e-9 else (0.0, 0.0)

        # Sharp endpoints: arcStart = arcEnd = vertex. Interior vertices round
        # like closed corners (index mapped back to original vertex order for
        # sharpCorners, matching buildPoints' reversed iteration).
        arcStart = list(rev)
        arcEnd = list(rev)
        if frac > 0:
            for i in range(1, n - 1):
                maxR = min(dist(rev[i], rev[i - 1]), dist(rev[i], rev[i + 1])) * 0.5
                r = 0 if (n - 1 - i) in self.sharpCorners else frac * maxR
                uIn = unit(rev[i], rev[i - 1])
                uOut = unit(rev[i], rev[i + 1])
                arcStart[i] = (rev[i][0] + uIn[0] * r, rev[i][1] + uIn[1] * r)
                arcEnd[i] = (rev[i][0] + uOut[0] * r, rev[i][1] + uOut[1] * r)

        bezier = []
        for i in range(n - 1):
            if arcStart[i] != arcEnd[i]:
                # Rounded corner: curve from arcStart through the vertex to arcEnd.
                bezier.append(arcStart[i])
                bezier.append(rev[i])
            mid = ((arcEnd[i][0] + arcStart[i + 1][0]) / 2, (arcEnd[i][1] + arcStart[i + 1][1]) / 2)
            bezier.append(arcEnd[i])
            bezier.append(mid)
        if arcStart[n - 1] != arcEnd[n - 1]:
            bezier.append(arcStart[n - 1])
            bezier.append(rev[n - 1])
        # Terminal anchor + dummy handle to keep the even pair format.
        bezier.append(arcEnd[n - 1])
        bezier.append(arcEnd[n - 1])
        return bezier

    def contains(self, x: wnumber, y: wnumber) -> bool:
        # Imported lazily: shapely drags in numpy (~60ms of startup), and this
        # is the only place it's used.
        import shapely.geometry as geo

        sx = self.meta.scale.x
        sy = self.meta.scale.y
        if sx == 0 or sy == 0:
            return False

        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]
        pivot_x = min(xs) + (max(xs) - min(xs)) * self.meta.align.x
        pivot_y = min(ys) + (max(ys) - min(ys)) * self.meta.align.y

        dx = x - self.meta.position.x
        dy = y - self.meta.position.y

        rad = self.meta.rotation * math.pi / 180
        dx_r = dx * math.cos(rad) + dy * math.sin(rad)
        dy_r = -dx * math.sin(rad) + dy * math.cos(rad)

        local_x = dx_r / sx + pivot_x
        local_y = dy_r / sy + pivot_y

        return geo.Polygon([*self.vertices]).contains(geo.Point(local_x, local_y))
