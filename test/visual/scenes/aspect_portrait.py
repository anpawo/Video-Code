#!/usr/bin/env python3

# Visual regression scene — a non-16:9 render.
#
# The suite renders this case at 1080x1920 — pinned in VisualTest's
# kGoldenCases, since a scene has no say over the resolution (--width/--height
# do). The golden is that size, so a resolution that failed to reach the
# encoder fails on frame size alone. The content checks the two halves that have to
# agree for anything to land where it belongs: the world->pixel origin
# (config::screenOffset) and the NDC divisor (MeshFactory). Mismatch them and
# the circle drifts off-center and the corner squares leave the frame — the
# exact failure the hardcoded 1920x1080 offset used to produce.

from videocode import *

BG = rgba(12, 20, 48)

# Dead center — the world origin.
Circle(radius=1.2, fillColor=rgba(255, 190, 60), strokeColor=TRANSPARENT).position(0, 0)

# Flush into all four corners of a 9x16 world, half in frame each.
for x in (-WORLD_OFFSET_X, WORLD_OFFSET_X):
    for y in (-WORLD_OFFSET_Y, WORLD_OFFSET_Y):
        Rectangle(width=2, height=2, fillColor=WHITE, strokeColor=TRANSPARENT).position(x, y)

# Full-width band: as wide as the world, so any world-size drift clips it.
Rectangle(width=WORLD_WIDTH, height=0.8, fillColor=rgba(90, 160, 255), strokeColor=TRANSPARENT).position(0, 4)
