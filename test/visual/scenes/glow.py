#!/usr/bin/env python3

# Visual regression scene — glow/bloom fragment effect.
# Glow blurs a copy of the input and additively composites it back onto the
# sharp original, producing a halo. Bright shapes on the default dark
# background make the halo unmistakable (a flat gradient would wash it out).
#
# Left circle has NO glow (reference); the others glow with growing radius +
# intensity, so a broken pass fails obviously (no halo, or the sharp core lost).

from videocode import *

CYAN = rgba(90, 220, 235)

# Reference — no glow.
Circle(radius=0.8, fillColor=YELLOW, strokeColor=TRANSPARENT).position(-4.5, 1.6)

# Moderate glow.
Circle(radius=0.8, fillColor=YELLOW, strokeColor=TRANSPARENT).position(0, 1.6) \
    .apply(glow(radius=9, intensity=1.0), duration=1)

# Strong, wide glow.
Circle(radius=0.8, fillColor=CYAN, strokeColor=TRANSPARENT).position(4.5, 1.6) \
    .apply(glow(radius=15, intensity=1.4), duration=1)

# Text glow — thin strokes benefit most from a halo, and the sharp glyph
# edges must survive underneath the bloom.
Text("GLOW", fontSize=1.1, fillColor=WHITE).position(0, -1.8) \
    .apply(glow(radius=11, intensity=1.1), duration=1)
