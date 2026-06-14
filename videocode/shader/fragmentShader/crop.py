#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import percent


class crop(FragmentShader):
    """
    Crop an `Input` to a rectangle relative to its own bounding box.

    `left`/`right`/`top`/`bottom` are percentages (0-100) of the bounding box
    cut away from each side. Cropped-out pixels become fully transparent
    (pixel masking) — the `Input`'s geometry/position is unchanged.
    """

    def __init__(
        self,
        left: percent = 0,
        right: percent = 0,
        top: percent = 0,
        bottom: percent = 0,
    ):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
