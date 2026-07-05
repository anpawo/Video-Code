#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class vhs(FragmentShader):
    """
    Retro VHS look: horizontal scanlines, a slight chromatic shift, analog
    noise and a per-frame vertical tracking jitter. Time-driven — the noise
    and jitter re-roll every frame over the effect's duration.

    - `intensity`: 0-1, scales every sub-effect at once.

    Example: `img.apply(vhs(), duration=2)`
    """

    def __init__(self, intensity: number = 0.6):
        self.intensity = intensity
