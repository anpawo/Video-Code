#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class grain(FragmentShader):
    """Add film grain noise."""

    def __init__(self, amount: unumber = 0.02):
        self.amount = amount
