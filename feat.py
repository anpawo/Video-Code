#!/usr/bin/env python3

# feat.py shows ONE example per effect in the *newest* batch only (project
# convention — keep it focused, don't accumulate every past batch here).
#
# Newest batch: per-input blend modes. Each shape's .blendMode(...) controls how
# its pixels combine with whatever is drawn behind it. A warm base rectangle is
# drawn normally; a cool rectangle overlaps its right half with a given mode, so
# the OVERLAP region shows the effect.
# Render with: ./video-code --file feat.py --generate feat.mp4

from videocode import *
from videocode.shader.vertexShader.blendMode import blendModeName

WARM = rgba(200, 120, 80)
COOL = rgba(80, 140, 220)

demos: list[tuple[blendModeName, str, float]] = [
    ("normal", 'blendMode("normal") — cool covers warm', -6.0),
    ("multiply", 'blendMode("multiply") — overlap darkens', -2.0),
    ("screen", 'blendMode("screen") — overlap lightens', 2.0),
    ("add", 'blendMode("add") — overlap clips to white', 6.0),
]

for mode, caption, x in demos:
    Text(mode, fontSize=0.28, fillColor=WHITE).position(x, 2.7)
    Rectangle(width=2.6, height=2.6, fillColor=WARM, strokeColor=TRANSPARENT) \
        .position(x - 0.7, 0.4)
    Rectangle(width=2.6, height=2.6, fillColor=COOL, strokeColor=TRANSPARENT) \
        .position(x + 0.7, 0.4).blendMode(mode)
    Text(caption, fontSize=0.13, fillColor=WHITE | 0.6).position(x, -1.6)
