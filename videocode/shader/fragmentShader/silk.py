#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.fragmentShader.mathShader import mathShader
from videocode.ty import unumber


__all__ = ["silk", "SILK_GLSL"]


SILK_GLSL = "assets/mathshaders/silk.glsl"


def silk(speed: unumber = 1.0, quality: unumber = 1.0) -> mathShader:
    """
    Raymarched sine-turbulence silk, ported from fragcoord.xyz (original
    shader: https://fragcoord.xyz/s/ae4trrxh) — a bundled preset of
    `mathShader` (which is where the pixels-replacement/matte semantics and
    the GLSL contract are documented):

        title = Text("SILK", fontSize=2, fillColor=silk())

    - `speed`: time multiplier (1.0 = the original shader's clock; 0 freezes
      the pattern on its first frame).
    - `quality`: 0..1, scales the raymarch step count (1.0 = the original's
      99 steps). The march dominates the cost — ~0.5 halves the GPU time at
      the price of a dimmer, softer pattern. Drop it for real-time preview,
      keep 1.0 for the final render.

    Cost note — this is an intrinsically heavy shader (~600 sin iterations
    per covered pixel; fragcoord.xyz only feels fast because a browser
    canvas is a fraction of 1080p). Measured on an Apple-Silicon GPU at
    1080p, quality=1.0: ~51ms/frame for a full-frame host, ~12ms for a
    quarter-frame one — zero-alpha pixels early-out, so cost is proportional
    to the host shape's coverage, NOT the frame. For a smooth preview: size
    the canvas to what the matte will reveal, and/or pass quality=0.3-0.5.
    """
    return mathShader(SILK_GLSL, speed=speed, quality=quality)
