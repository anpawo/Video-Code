#!/usr/bin/env python3


import math
from abc import abstractmethod

from videocode.input.input import Input
from videocode.utils.decorators import inputCreation, setAttrOn, autoProp, trackProps
from videocode.ty import *
from videocode.constants import *
from videocode.utils.logger import DEBUG


class Polygon(Input):
    cppName = "Polygon"
    cppAttrs = {
        "points",
        "fillColor",
        "strokeColor",
        "strokeWidth",
    }

    @trackProps
    @inputCreation
    def __init__(
        self,
        vertices: list[point],
        fillColor: rgba,
        strokeColor: rgba,
        strokeWidth: wufloat,
        cornerRadius: percent,
        sharpCorners: set[int] | frozenset[int] = frozenset(),
    ):
        self.vertices = vertices
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth
        self.sharpCorners = sharpCorners
        self.points = self.roundCorners()

    @abstractmethod
    def generateVertices(self) -> list[point]: ...

    @setAttrOn
    def updatePoints(self):
        self.vertices = self.generateVertices()
        self.points = self.roundCorners()

    @autoProp(updatePoints)
    def cornerRadius(self) -> percent: ...

    def roundCorners(self) -> list[point]:
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
        return bezier
