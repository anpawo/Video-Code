#!/usr/bin/env python3


from videocode.constants import RED_C, WHITE, rgba, wufloat
from videocode.input.input import Input
from videocode.ty import rgba, wufloat
from videocode.utils.decorators import inputCreation
from videocode.ty import *
from videocode.constants import *


class Circle(Input):
    cppName = "Circle"
    cppAttrs = {
        "radius",
        "fillColor",
        "strokeColor",
        "strokeWidth",
    }

    @inputCreation
    def __init__(
        self,
        radius: wufloat = 1,
        fillColor: rgba = RED_C,
        strokeColor: rgba = WHITE,
        strokeWidth: wufloat = 0.05,
    ):
        self.radius = radius
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth


class Dot(Circle):
    def __init__(
        self,
        radius: float = 0.0375,
        fillColor: rgba = RED_C,
    ):
        super().__init__(
            radius=radius,
            fillColor=fillColor,
            strokeColor=TRANSPARENT,
            strokeWidth=0,
        )
