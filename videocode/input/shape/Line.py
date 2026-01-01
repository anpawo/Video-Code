#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.input.shape.shape import *


class line(Shape):
    @inputCreation
    def __init__(
        self,
        length: wufloat = 3,
        thickness: wufloat = 0.05,
        color: rgba = WHITE,
        rounded: bool = False,
    ):
        self.length = length
        self.thickness = thickness
        self.color = color
        self.rounded = rounded
