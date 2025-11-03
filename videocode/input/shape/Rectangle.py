#!/usr/bin/env python3


from videocode.input.shape._Shape import *
from videocode.Decorators import inputCreation


class rectangle(Shape):
    width: uint
    height: uint
    thickness: uint
    color: rgba
    cornerRadius: uint
    filled: bool

    @inputCreation
    def __init__(
        self,
        width: uint = 400,
        height: uint = 200,
        thickness: uint = 20,
        color: rgba = GREEN,
        cornerRadius: uint = 0,  # 0 <= cornerRadius <= 90
        filled: bool = False,
    ): ...


class square(Shape):
    def __new__(
        cls,
        side: uint = 200,
        thickness: uint = 5,
        color: rgba = BLUE,
        cornerRadius: uint = 0,  # 0 <= cornerRadius <= 90
        filled: bool = False,
    ) -> rectangle:
        return rectangle(width=side, height=side, thickness=thickness, color=color, cornerRadius=cornerRadius, filled=filled)

    def __init__(self): ...
