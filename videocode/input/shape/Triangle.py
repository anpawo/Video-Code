#!/usr/bin/env python3

import math

from videocode.input.shape.Polygon import *
from videocode.utils.decorators import autoProp, trackProps


class Triangle(Polygon):
    @trackProps
    def __init__(
        self,
        p0: point = (0, 0),
        p1: point = (2, 0),
        p2: point = (3, 2),
        fillColor: rgba = DARK_BLUE,
        strokeColor: rgba = WHITE,
        strokeWidth: wufloat = 0.05,
        cornerRadius: percent = 0,
    ):
        super().__init__(
            vertices=self.generateVertices(),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )

    def generateVertices(self) -> list[point]:
        return [self.p0, self.p1, self.p2]

    @autoProp(Polygon.updatePoints)
    def p0(self, value: point): ...

    @autoProp(Polygon.updatePoints)
    def p1(self, value: point): ...

    @autoProp(Polygon.updatePoints)
    def p2(self, value: point): ...


class EquilateralTriangle(Triangle):
    @trackProps
    def __init__(
        self,
        side: wufloat = 3,
        fillColor: rgba = DARK_BLUE,
        strokeColor: rgba = WHITE,
        strokeWidth: wufloat = 0.05,
        cornerRadius: percent = 0,
    ):
        s = side
        h = s * math.sqrt(3) / 2
        super().__init__(
            p0=(0, 0),
            p1=(s, 0),
            p2=(s / 2, h),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )

    def generateVertices(self) -> list[point]:
        s = self.side
        h = s * math.sqrt(3) / 2
        return [(0, 0), (s, 0), (s / 2, h)]

    @autoProp(Polygon.updatePoints)
    def side(self, value: wufloat): ...


class RightTriangle(Triangle):
    @trackProps
    def __init__(
        self,
        width: wufloat = 4,
        height: wufloat = 3,
        fillColor: rgba = DARK_BLUE,
        strokeColor: rgba = WHITE,
        strokeWidth: wufloat = 0.05,
        cornerRadius: percent = 0,
    ):
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

    @autoProp(Polygon.updatePoints)
    def width(self, value: wufloat): ...

    @autoProp(Polygon.updatePoints)
    def height(self, value: wufloat): ...
