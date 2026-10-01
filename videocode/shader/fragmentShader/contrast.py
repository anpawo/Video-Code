#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class contrast(FragmentShader):
    """
    Contrast adjustment pivoting around mid-gray.

    - `amount`: -255 (flattest) .. 255 (most contrasted), 0 = unchanged.

    Example: `video.apply(contrast(60), duration=3)`
    """

    def __init__(self, amount: number = 0):
        self.amount = amount
