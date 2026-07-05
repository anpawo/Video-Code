#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class posterize(FragmentShader):
    """
    Reduce each color channel to `levels` discrete steps — smooth gradients
    become flat poster bands (screen-print / pop-art look).

    - `levels`: number of steps per channel (2 = extreme, 4-6 = classic).

    Example: `img.apply(posterize(4), duration=3)`
    """

    def __init__(self, levels: number = 4):
        self.levels = levels
