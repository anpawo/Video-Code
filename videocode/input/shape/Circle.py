#!/usr/bin/env python3


from videocode.input.input import Input
from videocode.utils.decorators import inputCreation
from videocode.ty import *
from videocode.constants import *


class Circle(Input):
    @inputCreation
    def __init__(
        self,
        radius: wufloat = 1,
        fillColor: rgba = RED_C,
        strokeColor: rgba = WHITE,
        strokeWidth: wufloat = 0.05,
    ):
        self.meta.name = "Circle"

        self.radius = radius
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth
