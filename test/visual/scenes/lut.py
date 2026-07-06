#!/usr/bin/env python3

# Visual regression scene — LUT color grade (.apply(lut("file.cube"))).
#
# A LUT remaps every pixel's color through a .cube 3D lookup table. To make the
# grade unmistakable (and a broken pass fail obviously), the SAME rainbow
# gradient is shown three times:
#   top    — no LUT (reference)
#   middle — identity16.cube: must look IDENTICAL to the reference (proves the
#            atlas layout + trilinear sampling round-trip a no-op LUT)
#   bottom — warm.cube: a warm cinematic grade (reds/greens lifted, blues
#            crushed) — visibly warmer/oranger, with the blue end darkened.
#
# A BROKEN LUT fails obviously: the identity row differs from the reference
# (wrong atlas UVs / channel swap), or the warm row is unchanged / garbage. So
# eyeball the golden — don't trust the run.

from videocode import *

RAINBOW = LinearGradient(
    rgba(255, 40, 40),
    rgba(255, 210, 40),
    rgba(60, 230, 120),
    rgba(60, 150, 255),
    rgba(210, 70, 255),
)

# Reference — no grade.
Rectangle(width=12, height=1.6, fillColor=RAINBOW, strokeColor=TRANSPARENT) \
    .position(0, 2.2)

# Identity LUT — must be visually identical to the reference row above.
Rectangle(width=12, height=1.6, fillColor=RAINBOW, strokeColor=TRANSPARENT) \
    .position(0, 0) \
    .apply(lut("assets/luts/identity16.cube"), duration=1)

# Warm cinematic grade — obviously shifted (warmer, blues crushed).
Rectangle(width=12, height=1.6, fillColor=RAINBOW, strokeColor=TRANSPARENT) \
    .position(0, -2.2) \
    .apply(lut("assets/luts/warm.cube"), duration=1)
