#!/usr/bin/env python3


from videocode.input.shape.Rectangle import *


class square(Shape):
    def __new__(
        cls,
        side: wufloat = 2,
        thickness: wufloat = 0.05,
        color: rgba = BLUE,
        cornerRadius: degree = 0,  # 0 <= cornerRadius <= 90
        filled: bool = False,
    ) -> rectangle:
        return rectangle(width=side, height=side, thickness=thickness, color=color, cornerRadius=cornerRadius, filled=filled)

    def __init__(self): ...


# set property side
