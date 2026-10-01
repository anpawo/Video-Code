#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class brightness(FragmentShader):
    """
    Adds a constant offset to every color channel.

    - `amount`: -255 (darkest) .. 255 (brightest), 0 = unchanged.

    Example: `video.apply(brightness(40), duration=3)`
    """

    def __init__(self, amount: number = 0):
        self.amount = amount
