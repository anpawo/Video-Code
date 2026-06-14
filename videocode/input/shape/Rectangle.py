#!/usr/bin/env python3

from __future__ import annotations

from videocode.input.shape.Polygon import *
from videocode.utils.decorators import prop
from videocode.utils.logger import *


class Rectangle(Polygon):
    def __init__(
        self,
        width: wunumber = 3,
        height: wunumber = 2,
        fillColor: rgba = BLUE_C | BLACK,
        strokeColor: rgba = BLUE_C | WHITE,
        strokeWidth: wunumber = 0.05,
        cornerRadius: percent = 0,  # percent 0-100, 100 = circle on a square
    ):
        self.width = width
        self.height = height

        super().__init__(
            vertices=self.generateVertices(),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )

    def generateVertices(self) -> list[point]:
        return [
            (0, 0),
            (self.width, 0),
            (self.width, self.height),
            (0, self.height),
        ]

    @prop(onSet=Polygon.updatePoints)
    def width() -> wunumber: ...

    @prop(onSet=Polygon.updatePoints)
    def height() -> wunumber: ...


class Square(Rectangle):
    def __init__(
        self,
        side: wunumber = 2,
        strokeWidth: wunumber = 0.05,
        fillColor: rgba = GREEN_A | BLACK,
        strokeColor: rgba = GREEN_A | WHITE,
        cornerRadius: percent = 0,
    ):
        super().__init__(
            width=side,
            height=side,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )


class HorizontalLine(Rectangle):
    """
    Horizontal Line
    """

    def __init__(
        self,
        length: wunumber = 3,
        strokeWidth: wunumber = 0.025,
        fillColor: rgba = BLUE_A,
        strokeColor: rgba = TRANSPARENT,
        rounded: bool = True,
    ):
        super().__init__(
            width=length,
            height=strokeWidth,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth / 3,
            cornerRadius=100 if rounded else 0,
        )

    @property
    def length(self):
        return self.width

    @length.setter
    def length(self, value: wnumber):
        self.width = value


class VerticalLine(Rectangle):
    """
    Vertical Line
    """

    def __init__(
        self,
        length: wunumber = 3,
        strokeWidth: wunumber = 0.025,
        fillColor: rgba = BLUE_A,
        strokeColor: rgba = TRANSPARENT,
        rounded: bool = True,
    ):
        super().__init__(
            height=length,
            width=strokeWidth,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth / 3,
            cornerRadius=100 if rounded else 0,
        )

    @property
    def length(self):
        return self.height

    @length.setter
    def length(self, value: wnumber):
        self.height = value
