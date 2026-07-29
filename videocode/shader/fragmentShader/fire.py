#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.fragmentShader.mathShader import mathShader
from videocode.ty import point, unumber


__all__ = ["fire", "FIRE_GLSL"]


FIRE_GLSL = "assets/mathshaders/fire.glsl"


def fire(speed: unumber = 1.0, quality: unumber = 1.0, scale: unumber = 1.0, origin: point = (50, 50), pixels: bool = False) -> mathShader:
    """
    "3D Fire" by @XorDev (Shadertoy) — a raymarched cone of sine-turbulence
    flames; a bundled preset of `mathShader` (which documents the
    pixels-replacement/matte semantics and the GLSL contract):

        title = Text("FIRE", fontSize=2, fillColor=fire())   # flames through text

    - `speed`: time multiplier (0 freezes the flame on its first frame).
    - `quality`: 0..1, scales the raymarch step count (1.0 = the original's
      50 steps); near-linear cost, dimmer/softer when lowered.
    - `scale`: zoom of the pattern — <1 shrinks it, so more of it fits.
    - `origin`: where the pattern is centred inside its HOST, as a percentage
      of the host's bounding box — `(50, 50)`, the default, is its middle, so
      a shaped host shows the middle of the pattern rather than whatever fell
      on that part of the frame. `pixels=True` reads it as pixels from the
      box's top-left instead.

    Cost — measurably lighter than `silk` but still a raymarcher: ~41ms/frame
    full-frame at 1080p on an Apple-Silicon GPU vs silk's ~60ms (50 march
    steps vs 99). Same scaling rules: zero-alpha pixels early-out, so cost is
    proportional to the host shape's coverage, and `quality` trades steps for
    speed. Size the host to what you'll actually show.
    """
    return mathShader(FIRE_GLSL, speed=speed, quality=quality, scale=scale, origin=origin, pixels=pixels)
