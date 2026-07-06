#!/usr/bin/env python3

# Visual regression scene — per-input blend modes.
# Four columns, each a warm base rectangle (drawn normal) with a cool top
# rectangle overlapping its right half. Only the top rectangle's blend mode
# changes between columns, so the OVERLAP region is the tell:
#   normal   → top color covers the base (opaque cool)
#   multiply → overlap darkens (product of the two colors → dark bluish gray)
#   screen   → overlap lightens (light lavender)
#   add      → overlap clips toward white (both channels sum past 1.0)
# The base + top colors are deliberately mid-range (not saturated primaries)
# so screen and add produce visibly different results.

from videocode import *

WARM = rgba(200, 120, 80)
COOL = rgba(80, 140, 220)

COLS: list[tuple[BlendMode, float]] = [
    (BlendMode.NORMAL, -6.0),
    (BlendMode.MULTIPLY, -2.0),
    (BlendMode.SCREEN, 2.0),
    (BlendMode.ADD, 6.0),
]

for mode, x in COLS:
    Text(mode.name.lower(), fontSize=0.3, fillColor=WHITE).position(x, 2.6)
    # Base: drawn normally, shifted left.
    Rectangle(width=2.6, height=2.6, fillColor=WARM, strokeColor=TRANSPARENT) \
        .position(x - 0.7, 0.5)
    # Top: overlaps the base's right half, composited with this column's mode.
    Rectangle(width=2.6, height=2.6, fillColor=COOL, strokeColor=TRANSPARENT) \
        .position(x + 0.7, 0.5).blendMode(mode)
