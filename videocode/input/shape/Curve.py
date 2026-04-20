#!/usr/bin/env python3


from typing import TYPE_CHECKING, Callable

from videocode.input.shape.shape import *
from videocode.utils.decorators import inputCreation, sandboxFlush, setAttrOn
from videocode.constants import WORLD_TO_SCREEN_RATIO as W2R


if TYPE_CHECKING:
    from videocode.template.input.Graph import Graph


class Curve(Shape):
    @inputCreation
    def __init__(
        self,
        points: list[tuple[number, number]],
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
            t = i / (n - 1) if n > 1 else 1.0
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
        parentGraph: Graph,
        numPoints: int = 100,
        strokeColor: rgba = BLUE_A,
        strokeWidth: wufloat = 0.025,
        onGraph=True,
    ):
        self.f = f
        self.parentGraph = parentGraph
        self.numPoints = numPoints
        self.xRange = xRange
        self.onGraph = onGraph

        super().__init__(
            points=self.generatePoints(),
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
        )

        self.alignOnGraph()

    def update(self, f: maybe[lambdaFunction] = None, numPoints: maybe[int] = None, xRange: maybe[tuple[int, int]] = None):
        if f is not None:
            self.f = f
        if numPoints is not None:
            self.numPoints = numPoints
        if xRange is not None:
            self.xRange = xRange

        points = self.generatePoints()
        self.alignOnGraph()

        with self:
            self.points = points
            self.flush()

    def alignOnGraph(self):
        if self.onGraph:
            self.align(0, 0).position(self.parentGraph.origin.x + self.xRange[0], self.parentGraph.origin.y + max(self.ys))

    def generatePoints(self) -> list[tuple[number, number]]:
        self.xs = [self.xRange[0] + i * (self.xRange[1] - self.xRange[0]) / (self.numPoints - 1) for i in range(self.numPoints)]
        self.ys = [self.f(x) for x in self.xs]
        return [(x * W2R, -y * W2R) for x, y in zip(self.xs, self.ys)]
