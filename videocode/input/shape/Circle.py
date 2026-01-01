#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.constants import *
from videocode.input.shape.shape import *


class circle(Shape):
    @inputCreation
    def __init__(
        self,
        radius: int = 100,
        thickness: int = 5,
        color: rgba = RED,
        filled: bool = False,
    ):
        self.radius = radius
        self.thickness = thickness
        self.color = color
        self.filled = filled
