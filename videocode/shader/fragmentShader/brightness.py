#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import int8


class brightness(FragmentShader):
    """
    Brightness filter.

    Adds a constant offset to all color channels (linear operation).

    - amount ∈ [-255, 255]
    - 0   : no effect
    - > 0 : brighter
    - < 0 : darker

    Equivalent to OpenCV:
        mat.convertTo(mat, -1, 1.0, amount)
    """

    def __init__(
        self,
        amount: int8,
    ):
        self.amount = amount
