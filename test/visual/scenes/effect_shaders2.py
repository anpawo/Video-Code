#!/usr/bin/env python3

# Visual regression scene — effects batch 2 fragment shaders.
# duotone: luminance remap between two colors (a gradient rect makes the
#   remap obvious — both ends recolor differently).
# vhs: time-driven scanlines + chroma shift + noise (deterministic per frame).
# zoomBlur: radial streaks from the bbox center — text shows the streak
#   direction unambiguously.

from videocode import *

Rectangle(width=3.5, height=2.2, fillColor=LinearGradient(WHITE, BLACK), strokeColor=TRANSPARENT) \
    .position(x=-3, y=1.5) \
    .apply(duotone(dark=BLUE_B, light=YELLOW), duration=1)

Rectangle(width=3.5, height=2.2, fillColor=LinearGradient(GREEN_A, BLUE_C), strokeColor=TRANSPARENT) \
    .position(x=3, y=1.5) \
    .apply(vhs(intensity=0.8), duration=1)

Text("ZOOM", fontSize=0.9, fillColor=WHITE).position(y=-1.5) \
    .apply(zoomBlur(0.3), duration=1)
