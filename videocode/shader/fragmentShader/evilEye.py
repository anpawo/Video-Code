#!/usr/bin/env python3

from __future__ import annotations

from videocode.color import rgba
from videocode.constants import Space
from videocode.shader.fragmentShader.mathShader import mathShader
from videocode.ty import maybe, point, unumber

__all__ = ["evilEye"]


EVIL_EYE_GLSL = "assets/mathshaders/evileye.glsl"


class evilEye(mathShader):
    """
    Burning slit-pupil eye, ported from the React Bits `<EvilEye />` WebGL
    component — a bundled preset of `mathShader` (which documents the
    pixels-replacement/matte semantics and the GLSL contract):

        eye = Rectangle(width=16, height=9, fillColor=evilEye())
        eye = Circle(radius=3, fillColor=evilEye(color=rgba("#7FD4FF")))

    - `color`: iris/flame colour.
    - `intensity`: brightness of that colour (HDR-ish, >1 blows out the core).
    - `pupilSize`: size and darkness of the slit.
    - `scale`: zoom, relative to the HOST SHAPE — 1.0 makes the shape's height
      the eye's own, <1 pulls the eye back inside it.
    - `speed`: flame flicker multiplier (0 freezes it).
    - `quality`: 0..1, octave count of the procedural flame noise (1.0 = the
      component's 8 octaves, 0 = 4 — the cheap end still reads as fire).

    One difference from the component, forced by the contract rather than
    chosen: it does NOT follow the cursor. A render has no cursor, and the
    effect is meant to stare straight at the viewer, so the pupil is fixed
    centre.

    The eye centres itself on its host shape and follows it — the C++ hands
    every math shader the host's screen-space box (p[0..3]) and this one builds
    its frame around it, so a shape that moves, scales or morphs takes the eye
    with it.

    `irisWidth`, `glowIntensity` and `noiseScale` from the component are baked
    at their defaults (0.25 / 0.35 / 1.0): 4 box + 3 origin + 7 args + the
    frame clock already fill 15 of the 24 push-constant slots, and the colour
    is packed into one float to keep it there.
    """

    def __init__(
        self,
        color: rgba = rgba("#FF6F37"),
        intensity: unumber = 1.5,
        pupilSize: unumber = 0.6,
        scale: unumber = 0.8,
        speed: unumber = 1.0,
        quality: unumber = 1.0,
        origin: point = (50, 50),
        pixels: bool = False,
        space: Space = Space.SHAPE,
        group: maybe[int] = None,
    ):
        super().__init__(
            EVIL_EYE_GLSL, speed=speed, quality=quality, scale=scale, origin=origin, pixels=pixels, space=space, group=group
        )
        # 0xRRGGBB in one float: a vec3 would cost three of the eight slots.
        # Exact — the value stays under 2^24, where float32 still counts by 1.
        self.color = float((color.r << 16) | (color.g << 8) | color.b)
        self.intensity = intensity
        self.pupilSize = pupilSize
