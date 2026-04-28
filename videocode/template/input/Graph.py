#!/usr/bin/env python3


from videocode import *


class Graph(Group):
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
        self.xRange = xRange
        self.yRange = yRange

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

        super().__init__(
            self.xAxis,
            self.yAxis,
            *self.numbers,
            *self.ticks,
        )


class FirstQuadrant(Graph):
    def __init__(
        self,
        xRange: tuple[int, int] = (-1, WORLD_WIDTH // 2),
        yRange: tuple[int, int] = (-1, WORLD_HEIGHT // 2),
        xExclude: list[int] = [-1],
        yExclude: list[int] = [-1],
    ) -> None:
        super().__init__(xRange, yRange, xExclude, yExclude)


class GraphPoint(Group):
    def __init__(
        self,
        curve: FunctionGraph,
        showTip=True,
        tipAbove=True,
    ) -> None:
        self.tipAppeared = False
        self.showTip = showTip
        self._tipAbove = tipAbove

        self.curve = curve
        self.tip: dummy[Offset[VerticalLine]] = Dummy()
        self.text: dummy[Offset[Text]] = Dummy()

        super().__init__(
            Group(Circle(0.09, fillColor=WHITE, strokeColor=BLACK, strokeWidth=0.015)),
        )

        if showTip:
            self.text = Offset(
                x=0,
                y=0.60 * (1 if self.tipAbove else -1),
                i=Text(text=str(round(self.curve.f(self.curve.xs[0]), 2)), color=WHITE, fontSize=0.2),
            )
            self.tip = Offset(
                x=0,
                y=0.30 * (1 if self.tipAbove else -1),
                i=VerticalLine(length=0.25, strokeWidth=0.025, fillColor=WHITE, rounded=True),
            )
            self.addInput(self.text, self.tip)

    @property
    def tipAbove(self) -> bool:
        return self._tipAbove

    @tipAbove.setter
    def tipAbove(self, value: bool):
        self._tipAbove = value
        self._updateTipPosition()

    def _updateTipPosition(self):
        if self.showTip:
            self.text.y = 0.60 * (1 if self.tipAbove else -1)
            self.tip.y = 0.30 * (1 if self.tipAbove else -1)

    def x(self, x: float) -> Self:
        y = self.curve.f(x)
        o = self.curve.parentGraph.origin

        self.position(x=x + o.x, y=y + o.y)
        self.fadeInIfHidden()
        self.flush()

        return self

    def fadeInIfHidden(self):
        if not self.tipAppeared:
            self.tipAppeared = True
            self.fadeIn(duration=0.2)

    def fromTo(self, x1: maybe[float] = None, x2: maybe[float] = None, duration: sec = 2) -> Self:
        x1 = self.curve.xs[0] if x1 is None else x1
        x2 = self.curve.xs[-1] if x2 is None else x2

        r = CubicBezier.range(Easing.InOut, x1, x2, duration)
        o = self.curve.parentGraph.origin

        self.position(x=x1 + o.x, y=self.curve.f(x1) + o.y)
        self.fadeInIfHidden()
        self.flush()

        with self.text.i:
            for x in r:
                y = self.curve.f(x)
                self.text.i.text = str(round(y, 2))
                self.position(x=x + o.x, y=y + o.y).flush()

        return self
