#!/usr/bin/env python3


from videocode.input.shape.Polygon import *
from videocode.utils.decorators import autoProp, trackProps
from videocode.utils.logger import *


class Rectangle(Polygon):
    @trackProps
    def __init__(
        self,
        width: wfloat = 5,
        height: wfloat = 3,
        fillColor: rgba = DARK_BLUE,
        strokeColor: rgba = WHITE,
        strokeWidth: wufloat = 0.05,
        cornerRadius: percent = 0,  # percent 0-100, 100 = circle on a square
    ):
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

    @autoProp(Polygon.updatePoints)
    def width(self, value: wfloat): ...

    @autoProp(Polygon.updatePoints)
    def height(self, value: wfloat): ...


class Square(Rectangle):
    def __init__(
        self,
        side: wfloat = 4,
        fillColor: rgba = DARK_BLUE,
        strokeColor: rgba = WHITE,
        strokeWidth: wufloat = 0.05,
        cornerRadius: float = 0,
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
        length: wfloat = 3,
        strokeWidth: wufloat = 0.025,
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


class VerticalLine(Rectangle):
    """
    Vertical Line
    """

    def __init__(
        self,
        length: wfloat = 3,
        strokeWidth: wufloat = 0.025,
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
