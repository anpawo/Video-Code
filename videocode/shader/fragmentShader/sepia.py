#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class sepia(FragmentShader):
    """
    Warm brown vintage tint — the old-photograph filter.

    - `amount`: 0-1, blends between the original colors and full sepia.

    Example: `img.apply(sepia(), duration=3)`
    """

    def __init__(self, amount: number = 1.0):
        self.amount = amount
