#!/usr/bin/env python3


from videocode.input.shape.shape import *
from videocode.utils.decorators import inputCreation


class Rectangle(Shape):
    @inputCreation
    def __init__(
        self,
        width: wufloat = 5,
        height: wufloat = 3,
        fillColor: rgba = DARK_BLUE,
        strokeColor: rgba = WHITE,
        strokeWidth: wufloat = 0.1,
        cornerRadius: float = 0,  # percent 0-100, 100 = circle on a square
    ):
        self.meta.name = "Rectangle"

        self.width = width
        self.height = height
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth
        self.cornerRadius = min(max(cornerRadius, 0), 100)


class Square(Rectangle):
    def __init__(
        self,
        side: wufloat = 2,
        fillColor: rgba = LIGHT_BLUE,
        strokeColor: rgba = BLUE,
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


class Line(Rectangle):
    def __init__(
        self,
        length: wufloat = 3,
        strokeWidth: wufloat = 0.1,
        fillColor: rgba = WHITE | BLUE,
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
