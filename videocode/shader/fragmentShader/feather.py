#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class feather(FragmentShader):
    """
    Fade an `Input` to transparent towards the edges of its own bounding box
    (Palmier Pro's "Edge Softness") — softens a hard clip boundary instead of
    cutting it.

    - `softness`: fraction (0-0.5) of the box's shorter side over which the
      fade happens.

    Example: `video.apply(feather(0.15), duration=3)`
    """

    def __init__(self, softness: number = 0.15):
        self.softness = softness
