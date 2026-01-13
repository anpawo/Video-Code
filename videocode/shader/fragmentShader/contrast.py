#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import int8


class contrast(FragmentShader):
    """
    Contrast filter.

    Adjusts contrast around the mid-gray value (128).

    - amount ∈ [-255, 255]
    - 0   : no effect
    - > 0 : higher contrast
    - < 0 : lower contrast
    """

    def __init__(
        self,
        amount: int8,
    ):
        self.amount = amount
