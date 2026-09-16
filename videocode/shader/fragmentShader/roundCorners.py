#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class roundCorners(FragmentShader):
    """
    Round the corners of an `Input`'s own bounding box — the classic
    rounded-video-clip look (Palmier Pro's "Edge Rounding").

    - `radius`: fraction (0-0.5) of the box's shorter side. 0.5 rounds a
      square input into a full circle.

    Example: `video.apply(roundCorners(0.1), duration=3)`
    """

    def __init__(self, radius: number = 0.1):
        self.radius = radius
