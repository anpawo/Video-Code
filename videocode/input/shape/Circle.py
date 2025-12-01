#!/usr/bin/env python3


from videocode.Decorators import inputCreation
from videocode.input.shape._Shape import *


class circle(Shape):
    radius: int
    thickness: int
    color: rgba
    filled: bool

    @inputCreation
    def __init__(
        self,
        radius: int = 100,
        thickness: int = 5,
        color: rgba = RED,
        filled: bool = False,
    ): ...
