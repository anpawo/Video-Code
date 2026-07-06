#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class grayscale(FragmentShader):
    """
    `Grayscale` an `Input`.

    - `strength`: 0-1, blends between the original and fully desaturated color
      (`p[0]` in grayscale/frag.glsl). Defaults to 1 (full grayscale) — without
      an explicit value the shader would otherwise read strength 0 (a no-op).
    """

    def __init__(self, strength: number = 1.0) -> None:
        self.strength = strength
