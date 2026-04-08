#!/usr/bin/env python3


import math

from constants import *
from videocode.videocode import *


class CartesianGraph:
    def __init__(self) -> None:
        lineThickness = 0.05

        self.xLine = (
            Line(
                length=0,
                strokeWidth=lineThickness,
                fillColor=WHITE | LIGHT_BLUE,
                strokeColor=TRANSPARENT,
                rounded=True,
            )
            .easeTo(16 * 0.9, "width", easing=Easing.InOut)
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
            .easeTo(9 * 0.9, "height", easing=Easing.InOut)
            .flush()
        )

        wait()

        self.numbers = []
        fontSize = 0.25
        y = -0.225
        x = y

        self.numbers.append(Text(text="0", fontSize=0).position(x * 0.9, y * 0.9).easeTo(fontSize, "fontSize").fadeIn())
        for i in range(1, 16 // 2 + 1):
            self.numbers.append(Text(text=str(i), fontSize=0).position(i * 0.9, y).easeTo(fontSize, "fontSize").fadeIn())
            self.numbers.append(Text(text=str(-i), fontSize=0).position(-i * 0.9, y).easeTo(fontSize, "fontSize").fadeIn())

        for i in range(1, 9 // 2 + 1):
            self.numbers.append(Text(text=str(i), fontSize=0).position(x, i * 0.9).easeTo(fontSize, "fontSize").fadeIn())
            self.numbers.append(Text(text=str(-i), fontSize=0).position(x, -i * 0.9).easeTo(fontSize, "fontSize").fadeIn())
