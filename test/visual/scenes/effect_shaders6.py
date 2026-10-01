#!/usr/bin/env python3

# Visual regression scene — effects batch 6: brightness/contrast/grain/sharpen
# rewrite. Each demo picks a fill a broken shader would leave visibly
# unchanged (flat gray, a smooth ramp, a flat fill, soft internal shading).

from videocode import *

# brightness: pushed bright — a broken shader leaves the gray unchanged.
Rectangle(width=2.2, height=2.2, fillColor=rgba(90, 90, 90), strokeColor=TRANSPARENT) \
    .position(x=-6.4, y=0).apply(brightness(120), duration=1)

# contrast: pushed hard — a broken shader leaves the gradient's soft ramp.
Rectangle(width=2.2, height=2.2, fillColor=LinearGradient(rgba(80, 80, 80), rgba(180, 180, 180)), strokeColor=TRANSPARENT) \
    .position(x=-3.2, y=0).apply(contrast(150), duration=1)

# grain: noise over a flat fill — a broken shader leaves it perfectly flat.
Rectangle(width=2.2, height=2.2, fillColor=rgba(120, 120, 120), strokeColor=TRANSPARENT) \
    .position(x=0, y=0).apply(grain(0.6), duration=1)

# sharpen: the same grain, then sharpened. A flat fill or a linear ramp has a
# zero Laplacian, so only per-pixel detail can show the kernel — the noise
# next door is that detail, and the difference between the two squares is the
# effect. A missing pipeline would leave the two identical.
Rectangle(width=2.2, height=2.2, fillColor=rgba(120, 120, 120), strokeColor=TRANSPARENT) \
    .position(x=3.2, y=0).apply(grain(0.6), duration=1).apply(sharpen(1.0), duration=1)

# outlives every sampled frame.
Rectangle(width=2.2, height=2.2, fillColor=rgba(200, 200, 200), strokeColor=TRANSPARENT) \
    .position(x=6.4, y=0).apply(brightness(-80), duration=1)
