#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class grain(FragmentShader):
    """
    Film-grain noise mixed into the image.

    - `amount`: 0 (unchanged) .. 1 (heaviest grain).

    Example: `video.apply(grain(0.2), duration=3)`
    """

    def __init__(self, amount: unumber = 0):
        self.amount = amount
