#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class zoomBlur(FragmentShader):
    """
    Radial (zoom) blur: pixels streak outward from the center of the
    `Input`'s own bounding box — the warp-speed / impact look.

    - `strength`: 0-1, how far along the center→pixel ray the samples spread
      (0.3+ is full warp-speed).

    Example: `img.apply(zoomBlur(0.25), duration=0.4)`
    """

    def __init__(self, strength: number = 0.15):
        self.strength = strength
