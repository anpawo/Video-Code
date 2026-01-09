#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class sharpen(FragmentShader):
    """Sharpen an input (amount 0..2)."""

    def __init__(self, amount: unumber = 0.5):
        self.amount = amount
