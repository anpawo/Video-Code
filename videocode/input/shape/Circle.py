#!/usr/bin/env python3


from videocode.input.shape.shape import *
from videocode.utils.decorators import inputCreation


class Circle(Shape):
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
