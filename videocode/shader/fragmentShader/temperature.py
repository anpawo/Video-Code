#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class temperature(FragmentShader):
    """
    White-balance-style color temperature shift: red and blue move in
    opposite directions while luma stays roughly constant.

    - `warmth`: -1 (cooler, bluer) .. 1 (warmer, more orange), 0 = unchanged.

    Example: `video.apply(temperature(0.4), duration=3)`
    """

    def __init__(self, warmth: number = 0.0):
        self.warmth = warmth
