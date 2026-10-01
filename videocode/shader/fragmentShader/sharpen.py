#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class sharpen(FragmentShader):
    """
    Unsharp-mask sharpening.

    - `amount`: 0 (unchanged) .. 1 (full kernel strength).

    Example: `video.apply(sharpen(0.5), duration=3)`
    """

    def __init__(self, amount: unumber = 0):
        self.amount = amount
