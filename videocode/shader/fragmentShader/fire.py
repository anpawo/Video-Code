#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.fragmentShader.mathShader import mathShader
from videocode.ty import unumber


__all__ = ["fire", "FIRE_GLSL"]


FIRE_GLSL = "assets/mathshaders/fire.glsl"


def fire(speed: unumber = 1.0, quality: unumber = 1.0) -> mathShader:
    """
    "3D Fire" by @XorDev (Shadertoy) — a raymarched cone of sine-turbulence
    flames; a bundled preset of `mathShader` (which documents the
    pixels-replacement/matte semantics and the GLSL contract):

        title = Text("FIRE", fontSize=2, fillColor=fire())   # flames through text

    - `speed`: time multiplier (0 freezes the flame on its first frame).
    - `quality`: 0..1, scales the raymarch step count (1.0 = the original's
      50 steps); near-linear cost, dimmer/softer when lowered.

    Cost — measurably lighter than `silk` but still a raymarcher: ~41ms/frame
    full-frame at 1080p on an Apple-Silicon GPU vs silk's ~60ms (50 march
    steps vs 99). Same scaling rules: zero-alpha pixels early-out, so cost is
    proportional to the host shape's coverage, and `quality` trades steps for
    speed. Size the host to what you'll actually show.
    """
    return mathShader(FIRE_GLSL, speed=speed, quality=quality)
