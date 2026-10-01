#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class chromaticAberration(FragmentShader):
    """
    RGB channel split, radiating from the frame's centre: red samples
    outward, blue samples inward, green stays in place — the lens-fringe
    look.

    - `amount`: shift as a fraction of frame width (typical 0.005).

    Example: `video.apply(chromaticAberration(0.006), duration=3)`
    """

    def __init__(self, amount: number = 0.005):
        self.amount = amount
