#!/usr/bin/env python3


from constants import *
from videocode.videocode import *


class CartesianGraph:
    def __init__(
        self,
        showNegativeX=True,
        showNegativeY=True,
        offset=0.9,
    ) -> None:
        lineThickness = 0.05

        self.xLine = (
            Line(
                length=0,
                strokeWidth=lineThickness,
                fillColor=WHITE | LIGHT_BLUE,
                strokeColor=TRANSPARENT,
                rounded=True,
            )
            .align(None if showNegativeX else 0, None if showNegativeY else 0)
            .position(0 if showNegativeX else WORLD_WIDTH * -offset / 2, 0 if showNegativeY else WORLD_HEIGHT * -offset / 2)
            .easeTo(WORLD_WIDTH * offset, "width", easing=Easing.InOut)
            .flush()
        )
        self.yLine = (
            Line(
                length=lineThickness,
                strokeWidth=0,
                fillColor=WHITE | LIGHT_BLUE,
                strokeColor=TRANSPARENT,
                rounded=True,
            )
            .align(None if showNegativeX else 0, None if showNegativeY else 0)
            # .rotate(0 if showNegativeY else 180)
            .position(0 if showNegativeX else WORLD_WIDTH * -offset / 2, 0 if showNegativeY else WORLD_HEIGHT * -offset / 2)
            .easeTo(WORLD_HEIGHT * -0.9, "height", easing=Easing.InOut)
            .flush()
        )

        wait()

        self.numbers = []
        fontSize = 0.25
        y = -0.225
        x = y

        self.numbers.append(Text(text="0", fontSize=0).position(x * 0.9, y * 0.9).easeTo(fontSize, "fontSize").fadeIn())
        for i in range(1, WORLD_WIDTH // 2 + 1):
            self.numbers.append(Text(text=str(i), fontSize=0).position(i * 0.9, y).easeTo(fontSize, "fontSize").fadeIn())
            self.numbers.append(Text(text=str(-i), fontSize=0).position(-i * 0.9, y).easeTo(fontSize, "fontSize").fadeIn())

        for i in range(1, WORLD_HEIGHT // 2 + 1):
            self.numbers.append(Text(text=str(i), fontSize=0).position(x, i * 0.9).easeTo(fontSize, "fontSize").fadeIn())
            self.numbers.append(Text(text=str(-i), fontSize=0).position(x, -i * 0.9).easeTo(fontSize, "fontSize").fadeIn())


class FirstQuadrantGraph(CartesianGraph):
    def __init__(self) -> None:
        super().__init__(
            showNegativeX=False,
            showNegativeY=False,
        )
