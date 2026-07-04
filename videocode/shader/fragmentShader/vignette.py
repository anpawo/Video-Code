#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number, percent


class vignette(FragmentShader):
    """
    Darken an `Input` toward the edges of its own bounding box — the classic
    photographic vignette.

    - `intensity`: maximum darkening at the corners (0-1).
    - `radius`: percentage (0-100) of the half-diagonal where the darkening
      begins — inside it the image is untouched.
    - `smoothness`: falloff width past `radius`, as a percentage — small
      values give a hard oval edge, large values a gentle gradient.

    Example: `img.apply(vignette(), duration=3)`
    """

    def __init__(
        self,
        intensity: number = 0.6,
        radius: percent = 45,
        smoothness: percent = 55,
    ):
        self.intensity = intensity
        self.radius = radius
        self.smoothness = smoothness
