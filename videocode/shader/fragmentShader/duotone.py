#!/usr/bin/env python3

from __future__ import annotations

from videocode.color import rgba
from videocode.constants import BLACK, WHITE
from videocode.ty import number
from videocode.shader.ishader import FragmentShader


class duotone(FragmentShader):
    """
    Two-color remap: the `Input`'s luminance is mapped between `dark` and
    `light` — shadows become `dark`, highlights become `light`. The Spotify-
    poster look.

    - `contrast` (0-1): pushes the luminance through an S-curve before the
      mix so pixels commit to one ink or the other. 0 = raw linear mix
      (mid tones become a mud blend of the two colors — usually ugly),
      1 = hard two-tone. Pick genuinely dark/light inks for the classic look.

    The colors are stored flattened as six float attributes (GLSL push
    constants only carry numbers, and params are ordered by attribute name):
    contrast, darkB, darkG, darkR, lightB, lightG, lightR → p[0..6].

    Example: `img.apply(duotone(dark=BLUE_B, light=YELLOW), duration=3)`
    """

    def __init__(self, dark: rgba = BLACK, light: rgba = WHITE, contrast: number = 0.7):
        self.contrast = contrast
        self.darkB = dark.b / 255.0
        self.darkG = dark.g / 255.0
        self.darkR = dark.r / 255.0
        self.lightB = light.b / 255.0
        self.lightG = light.g / 255.0
        self.lightR = light.r / 255.0
