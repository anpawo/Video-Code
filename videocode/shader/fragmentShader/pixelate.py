#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class pixelate(FragmentShader):
    """
    Quantize an `Input`'s pixels into square cells — mosaic / censor effect.

    - `size`: cell size in screen pixels.

    Animate it down to 1 for a "resolve from pixels" reveal:

        for s, i in Easing.Out.rangeIdx(48, 1, 0.8):
            img.apply(pixelate(s), start=i * SINGLE_FRAME)

    Example: `img.apply(pixelate(16), duration=2)`
    """

    def __init__(self, size: number = 12):
        self.size = size
