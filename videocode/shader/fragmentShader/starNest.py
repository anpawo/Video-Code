#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.fragmentShader.mathShader import mathShader
from videocode.ty import unumber


__all__ = ["starNest", "STAR_NEST_GLSL"]


STAR_NEST_GLSL = "assets/mathshaders/starnest.glsl"


def starNest(speed: unumber = 1.0, quality: unumber = 1.0) -> mathShader:
    """
    "Star Nest" by Pablo Roman Andrioli (Kali) — the famous volumetric
    fractal starfield/nebula (shadertoy.com/view/XlfGRj, MIT). A bundled
    preset of `mathShader` (which documents the pixels-replacement/matte
    semantics and the GLSL contract):

        Rectangle(width=16, height=9, fillColor=starNest())   # full-frame space background
        Text("STARS", fontSize=2, fillColor=starNest())       # a galaxy through text

    - `speed`: flight-speed multiplier (0 freezes the view).
    - `quality`: 0..1, scales the 20 volumetric steps.

    Cost — the cheapest of the raymarched presets, its loops being pure
    abs/dot/length math (no transcendentals): measured ~19ms/frame
    full-frame at 1080p vs fire's ~41ms and silk's ~60ms — usable as a
    full-frame animated background (drop `quality` if the preview stutters).
    Zero-alpha pixels early-out, so shaped hosts cost proportionally less.
    """
    return mathShader(STAR_NEST_GLSL, speed=speed, quality=quality)
