#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class invert(FragmentShader):
    """
    Color negative — every channel flipped.

    - `amount`: 0-1, blends between the original and the fully inverted
      colors (0.5 lands on flat gray, as it must).

    Example: `img.apply(invert(), start=1.0, duration=0.1)` — a 3-frame
    negative flash is a classic impact accent.
    """

    def __init__(self, amount: number = 1.0):
        self.amount = amount
