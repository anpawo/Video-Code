#!/usr/bin/env python3


from typing import TYPE_CHECKING, Callable, Self
from videocode.input.input import Input
from videocode.utils.bezier import Easing
from videocode.utils.decorators import inputCreation, setAttrOn
from videocode.ty import *
from videocode.constants import *


if TYPE_CHECKING:
    from videocode.template.input.Graph import Graph


class Curve(Input):
    cppAttrs = {
        "points",
        "strokeColor",
        "strokeWidth",
    }

    @inputCreation
    def __init__(
        self,
        points: list[point],
        strokeColor: rgba = WHITE,
        strokeWidth: wufloat = 0.025,
    ):
        self.meta.name = "Curve"

        self.points = points
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth

    # sandboxFlush
    @setAttrOn
    def animate(self, duration: sec = 0.4, easing=Easing.InOut) -> Self:
        allPoints = list(self.points)
        n = int(duration * FRAMERATE)
        lastCount = 0

        for i in range(n):
            t = i / (n - 1)
            count = max(2, round(easing(t) * len(allPoints)))
            if count != lastCount:
                self.points = allPoints[:count]
                lastCount = count
            self.flush()

        return self


type lambdaFunction = Callable[[number], number]


class FunctionGraph(Curve):
    def __init__(
        self,
        f: lambdaFunction,
        xRange: tuple[int, int],
        parentGraph: maybe[Graph] = None,
        numPoints: int = 100,
        strokeColor: rgba = BLUE_A,
        strokeWidth: wufloat = 0.025,
        alignOn=True,
    ):
        self.f = f
        self.parentGraph = parentGraph
        self.numPoints = numPoints
        self.xRange = xRange
        self.alignOn = alignOn

        # x => y
        self.xs = []
        self.ys = []

        super().__init__(
            points=self.generatePoints(),
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
        )

        self.alignOrdinate()

    @setAttrOn
    def update(self, f: maybe[lambdaFunction] = None, numPoints: maybe[int] = None, xRange: maybe[tuple[int, int]] = None):
        if f is not None:
            self.f = f
        if numPoints is not None:
            self.numPoints = numPoints
        if xRange is not None:
            self.xRange = xRange

        points = self.generatePoints()
        self.alignOrdinate()

        self.points = points
        self.flush()

    def alignOrdinate(self):
        if self.alignOn:
            if self.parentGraph is not None:
                self.align(0, 0).position(self.parentGraph.origin.x, self.parentGraph.origin.y)
            else:
                self.align(0, 0).position(y=-min(self.ys))

    def generatePoints(self) -> list[point]:
        self.xs = [self.xRange[0] + i * (self.xRange[1] - self.xRange[0]) / (self.numPoints - 1) for i in range(self.numPoints)]
        self.ys = [self.f(x) for x in self.xs]
        return [(x, y) for x, y in zip(self.xs, self.ys)]
