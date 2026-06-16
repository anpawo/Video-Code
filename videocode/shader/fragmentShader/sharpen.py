#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class sharpen(FragmentShader):
    """
    Sharpen filter.

    - amount ∈ [0, 1]
    - 0   : no effect
    - 1   : full sharpen kernel
    """

    def __init__(
        self,
        amount: unumber,
    ):
        self.amount = amount
