#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class halftone(FragmentShader):
    """
    Comic-book halftone: the `Input` is rebuilt from a 45°-rotated grid of
    dots whose size follows the local brightness — dark areas get big dots,
    highlights shrink to pinpricks. Dots keep the source color.

    - `size`: dot-grid cell size in screen pixels.

    Example: `img.apply(halftone(10), duration=3)`
    """

    def __init__(self, size: number = 10):
        self.size = size
