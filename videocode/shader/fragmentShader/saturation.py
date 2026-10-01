#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class saturation(FragmentShader):
    """
    Luma-based (Rec. 709) saturation control.

    - `amount`: 0 = grayscale, 1 = unchanged, 2 = doubled saturation.

    Example: `video.apply(saturation(1.4), duration=3)`
    """

    def __init__(self, amount: number = 1.0):
        self.amount = amount
