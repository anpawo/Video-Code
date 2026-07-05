#!/usr/bin/env python3

from __future__ import annotations

from videocode.color import rgba
from videocode.constants import GREEN
from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class chromaKey(FragmentShader):
    """
    Green-screen keying: pixels close to `color` become transparent.

    - `tolerance` (0-1): how close a pixel's hue/saturation must be to
      `color` to be keyed out. Higher = keys out a wider range of similar
      colors (may eat into the subject on cheap/uneven lighting).
    - `softness` (0-1): width of the transparency falloff at the edge of the
      keyed range — 0 gives a hard cutout, higher softens the edge (helps
      hide keying artifacts/color spill on hair, glass, etc).

    The color is stored flattened as three float attributes (push constants
    only carry numbers): keyB, keyG, keyR → p[0..2] (alphabetical).

    Example: `video.apply(chromaKey(color=GREEN, tolerance=0.35), duration=VIDEO_LEN)`
    """

    def __init__(self, color: rgba = GREEN, tolerance: number = 0.3, softness: number = 0.15):
        self.tolerance = tolerance
        self.softness = softness
        self.keyB = color.b / 255.0
        self.keyG = color.g / 255.0
        self.keyR = color.r / 255.0
