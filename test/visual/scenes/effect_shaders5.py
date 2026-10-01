#!/usr/bin/env python3

# Visual regression scene — effects batch 5: everyday explainer-video filters.
# letterbox sits BEHIND everything, full-frame, ratio wider than 16:9 so it
# bars top/bottom — the other five demos live in the untouched middle band,
# so a broken letterbox (no bars) and a broken foreground effect are both
# visible in the same frame without one hiding the other.

from videocode import *

Rectangle(width=W, height=H, fillColor=BLUE_C, strokeColor=TRANSPARENT) \
    .apply(letterbox(2.4), duration=1)

# roundCorners: a broken shader leaves the square corners untouched.
Rectangle(width=2.2, height=2.2, fillColor=RED_B, strokeColor=TRANSPARENT) \
    .position(x=-6.4, y=0).apply(roundCorners(0.3), duration=1)

# feather: fades into the letterbox background instead of cutting hard.
Rectangle(width=2.2, height=2.2, fillColor=GREEN_A, strokeColor=TRANSPARENT) \
    .position(x=-3.2, y=0).apply(feather(0.3), duration=1)

# saturation: fully desaturated — a broken shader keeps the gradient's color.
Rectangle(width=2.2, height=2.2, fillColor=LinearGradient(RED_B, GREEN_A), strokeColor=TRANSPARENT) \
    .position(x=0, y=0).apply(saturation(0.0), duration=1)

# temperature: strong warm push on a neutral gray.
Rectangle(width=2.2, height=2.2, fillColor=rgba(160, 160, 160), strokeColor=TRANSPARENT) \
    .position(x=3.2, y=0).apply(temperature(0.9), duration=1)

# chromaticAberration: RGB fringing at the glyph edges, over a dark backing
# so the shifted channels are unmistakable against transparency.
Rectangle(width=2.2, height=2.2, fillColor=rgba(20, 20, 20), strokeColor=TRANSPARENT) \
    .position(x=6.4, y=0)
Text("RGB", fontSize=0.9, fillColor=WHITE).position(x=6.4, y=0) \
    .apply(chromaticAberration(0.01), duration=1)
