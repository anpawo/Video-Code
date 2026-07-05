#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import degree


class hueRotate(FragmentShader):
    """
    Rotate every color's hue around the color wheel by `degrees` (CSS
    `hue-rotate`): 120° turns red into green into blue; 180° gives the
    complementary palette. Apply with increasing angles per frame for the
    classic RGB color-cycle loop.

    Example:
        img.apply(hueRotate(180), duration=3)
        for d, i in Easing.Linear.rangeIdx(0, 360, 2.0):   # color cycle
            img.apply(hueRotate(d), start=i * SINGLE_FRAME)
    """

    def __init__(self, degrees: degree = 90):
        self.degrees = degrees
