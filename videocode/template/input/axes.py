#!/usr/bin/env python3


import math

from constants import *
from videocode.constants import WORLD_HEIGHT, WORLD_WIDTH, rgba
from videocode.videocode import *
from videocode.videocode import WORLD_HEIGHT, WORLD_WIDTH, rgba


class Axes:
    def __init__(
        self,
        # --
        xRange: tuple[int, int] = (-7, 7),
        yRange: tuple[int, int] = (-4, 4),
        # --
        xExclude: list[int] = [],
        yExclude: list[int] = [],
        # --
        unitSize: number | tuple[number, number] = 1.0,
        # --
        labelOffset=-0.23,
        fontSize=0.25,
        # --
        color=rgba("#BBBBBB"),
        # --
        lineThickness=0.025,
    ) -> None:

        xExclude.append(0)
        yExclude.append(0)

        unitSizeX = unitSize[0] if isinstance(unitSize, tuple) else unitSize
        unitSizeY = unitSize[1] if isinstance(unitSize, tuple) else unitSize

        x = range(xRange[0], xRange[1] + 1)
        y = range(yRange[0], yRange[1] + 1)

        self.origin = v2((-(len(x) - 1) / 2 - xRange[0]) * unitSizeX, (-(len(y) - 1) / 2 - yRange[0]) * unitSizeY)

        self.xAxis = (
            Rectangle(
                width=0,
                height=lineThickness,
                fillColor=color,
                strokeColor=TRANSPARENT,
            )
            .align(x=0)
            .position(-(len(x) - 1) / 2 * unitSizeX, (-(len(y) - 1) / 2 - yRange[0]) * unitSizeY)
            .easeTo((len(x) - 1) * unitSizeX, "width", easing=Easing.InOut)
            .flush()
        )
        self.yAxis = (
            Rectangle(
                width=lineThickness,
                height=0,
                fillColor=color,
                strokeColor=TRANSPARENT,
            )
            .align(y=1)
            .position((-(len(x) - 1) / 2 - xRange[0]) * unitSizeX, -(len(y) - 1) / 2 * unitSizeY)
            .easeTo((len(y) - 1) * unitSizeY, "height", easing=Easing.InOut)
            .flush()
        )

        self.numbers: list[Input] = []
        self.ticks: list[Input] = []

        for n in x:
            start = 0.3 * (n - xRange[0]) / (xRange[1] - xRange[0])
            self.ticks.append(
                Rectangle(width=lineThickness, height=0, fillColor=color, strokeColor=TRANSPARENT)
                .position(
                    -(len(x) - 1) / 2 * unitSizeX + n * unitSizeX - xRange[0],
                    (-(len(y) - 1) / 2 - yRange[0]) * unitSizeY,
                )
                .easeTo(lineThickness * 5, "height", start=start, duration=0.15)
                .fadeIn(start=start, duration=0.15)
            )
            if n in xExclude:
                continue
            self.numbers.append(
                Text(text=str(n), fontSize=0)
                .align(x=0.75 if n < 0 else None)
                .position(
                    -(len(x) - 1) / 2 * unitSizeX + n * unitSizeX - xRange[0],
                    (-(len(y) - 1) / 2 - yRange[0]) * unitSizeY + labelOffset,
                )
                .easeTo(fontSize, "fontSize", start=start, duration=0.15)
                .fadeIn(start=start, duration=0.15)
            )

        for n in y:
            start = 0.3 * (n - yRange[0]) / (yRange[1] - yRange[0])
            self.ticks.append(
                Rectangle(width=0, height=lineThickness, fillColor=color, strokeColor=TRANSPARENT)
                .position(
                    (-(len(x) - 1) / 2 - xRange[0]) * unitSizeX,
                    -(len(y) - 1) / 2 * unitSizeY + n * unitSizeY - yRange[0],
                )
                .easeTo(lineThickness * 5, "width", start=start, duration=0.15)
                .fadeIn(start=start, duration=0.15)
            )
            if n in yExclude:
                continue
            self.numbers.append(
                Text(text=str(n), fontSize=0)
                .position(
                    (-(len(x) - 1) / 2 - xRange[0]) * unitSizeX + labelOffset,
                    -(len(y) - 1) / 2 * unitSizeY + n * unitSizeY - yRange[0],
                )
                .easeTo(fontSize, "fontSize", start=start, duration=0.15)
                .fadeIn(start=start, duration=0.15)
            )


class FirstQuadrant(Axes):
    def __init__(
        self,
        xRange: tuple[int, int] = (-1, WORLD_WIDTH // 2),
        yRange: tuple[int, int] = (-1, WORLD_HEIGHT // 2),
        xExclude: list[int] = [-1],
        yExclude: list[int] = [-1],
    ) -> None:
        super().__init__(xRange, yRange, xExclude, yExclude)
