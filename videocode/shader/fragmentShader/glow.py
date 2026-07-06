#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class glow(FragmentShader):
    """
    Add a `glow`/bloom halo to an `Input`.

    A blurred copy of the input is additively composited back on top of the
    sharp original, producing a soft halo. Works best on bright shapes against
    a dark background.

    - `radius`: blur kernel strength (reuses `blur`'s sigma semantics — odd and
      positive reads best).
    - `intensity`: how bright the additive halo is (1.0 = full).

    NOTE ON PARAM ORDER: the C++/GLSL side receives args ALPHABETICALLY, so the
    renderer reads params as `[intensity, radius]` (i before r), NOT the
    __init__ assignment order. The glow branch in both renderers depends on
    that order — see docs/ADDING_EFFECTS.md.
    """

    def __init__(
        self,
        radius: unumber = 5.0,
        intensity: unumber = 1.0,
    ):
        self.radius = radius
        self.intensity = intensity
