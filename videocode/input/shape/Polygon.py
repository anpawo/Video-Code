#!/usr/bin/env python3


import math
import shapely.geometry as geo

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
    ):
        self.vertices = vertices
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth
        self.cornerRadius = cornerRadius
        self.sharpCorners = sharpCorners
        self.points = self.buildPoints()

    @abstractmethod
    def generateVertices(self) -> list[point]: ...

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
        Build 4n bezier control points from self.vertices and self.cornerRadius.

        Iterates in reversed vertex order so C++ only needs to negate y (no reversal).

        Each corner produces: arcStart, cornerHandle, arcEnd, connectorMidpoint.
        """

        verts = self.vertices
        n = len(verts)
        if n < 2:
            return list(verts)

        frac = self.cornerRadius / 100.0
        rev = list(reversed(verts))

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
        return list(map(lambda x: (round(x[0], 6), round(x[1], 6)), bezier))

    def contains(self, x: wnumber, y: wnumber) -> bool:
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
