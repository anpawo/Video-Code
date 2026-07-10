#!/usr/bin/env python3

from __future__ import annotations

import math

from videocode.input.shape.Polygon import *
from videocode.utils.decorators import prop


class Triangle(Polygon):
    def __init__(
        self,
        p0: point = (0, 0),
        p1: point = (2, 0),
        p2: point = (3, 2),
        fillColor: paint = RED_B | BLACK,
        strokeColor: rgba = RED_B | WHITE,
        strokeWidth: wufloat = 0.05,
        cornerRadius: percent = 0,
    ):
        self.p0 = p0
        self.p1 = p1
        self.p2 = p2

        super().__init__(
            vertices=self.generateVertices(),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )

    def generateVertices(self) -> list[point]:
        return [self.p0, self.p1, self.p2]

    @prop(onSet=Polygon.updatePoints)
    def p0() -> point: ...

    @prop(onSet=Polygon.updatePoints)
    def p1() -> point: ...

    @prop(onSet=Polygon.updatePoints)
    def p2() -> point: ...


class EquilateralTriangle(Triangle):
    def __init__(
        self,
        side: wufloat = 3,
        fillColor: paint = RED_B | BLACK,
        strokeColor: rgba = RED_B | WHITE,
        strokeWidth: wufloat = 0.05,
        cornerRadius: percent = 0,
    ):
        self.side = side

        h = side * math.sqrt(3) / 2
        super().__init__(
            p0=(0, 0),
            p1=(side, 0),
            p2=(side / 2, h),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )

    def generateVertices(self) -> list[point]:
        s = self.side
        h = s * math.sqrt(3) / 2
        return [(0, 0), (s, 0), (s / 2, h)]

    @prop(onSet=Polygon.updatePoints)
    def side() -> wufloat: ...


class RightTriangle(Triangle):
    def __init__(
        self,
        width: wufloat = 4,
        height: wufloat = 3,
        fillColor: paint = RED_B | BLACK,
        strokeColor: rgba = RED_B | WHITE,
        strokeWidth: wufloat = 0.05,
        cornerRadius: percent = 0,
    ):
        self.width = width
        self.height = height

        super().__init__(
            p0=(0, 0),
            p1=(width, 0),
            p2=(0, height),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )

    def generateVertices(self) -> list[point]:
        return [(0, 0), (self.width, 0), (0, self.height)]

    @prop(onSet=Polygon.updatePoints)
    def width() -> wufloat: ...

    @prop(onSet=Polygon.updatePoints)
    def height() -> wufloat: ...
