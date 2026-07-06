# Visual regression scene — adjustment layers (Tier 2).
#
# AdjustmentLayer() grades the flattened composite of everything BELOW its
# zIndex, not its own (invisible) geometry. This scene proves three things at a
# glance — so a broken flatten fails obviously:
#
#   TOP row    (zIndex 1)  red / green / blue shapes, sitting BELOW both layers.
#   AL #1      (zIndex 5)  grayscale  -> the top row turns gray.
#   MIDDLE row (zIndex 6)  magenta / yellow / cyan, ABOVE AL #1 (stays colored
#                          w.r.t. #1) but BELOW AL #2.
#   AL #2      (zIndex 10) invert     -> grades EVERYTHING below zIndex 10: the
#                          already-gray top row (gray -> inverted gray) AND the
#                          colored middle row (color -> inverted color).
#   BOTTOM row (zIndex 20) orange shape, ABOVE every layer -> full, untouched
#                          color. This is the control: if grading leaked to the
#                          whole frame, this shape would change.
#
# So a correct render shows: top row grayscale-then-inverted, middle row
# inverted colors, bottom shape pure orange. Eyeball the golden — a scene-wide
# or wrongly-ordered grade is immediately visible.

from videocode import *

DUR = 1  # keep both grades active through the sampled frame 0

# --- TOP row (below both adjustment layers) ---
Circle(radius=1, fillColor=rgba(240, 40, 40), strokeColor=TRANSPARENT).position(-5, 3).zIndex(1)
Square(side=2, fillColor=rgba(40, 220, 40), strokeColor=TRANSPARENT).position(0, 3).zIndex(1)
Triangle(fillColor=rgba(50, 120, 255), strokeColor=TRANSPARENT).position(5, 3).zIndex(1)

# --- Adjustment layer #1: grayscale everything below zIndex 5 (the top row) ---
AdjustmentLayer().zIndex(5).apply(grayscale(), duration=DUR)

# --- MIDDLE row (above AL #1, below AL #2) ---
Circle(radius=1, fillColor=rgba(230, 40, 230), strokeColor=TRANSPARENT).position(-5, 0).zIndex(6)
Square(side=2, fillColor=rgba(240, 230, 40), strokeColor=TRANSPARENT).position(0, 0).zIndex(6)
Triangle(fillColor=rgba(40, 230, 230), strokeColor=TRANSPARENT).position(5, 0).zIndex(6)

# --- Adjustment layer #2: invert everything below zIndex 10 (top + middle) ---
AdjustmentLayer().zIndex(10).apply(invert(), duration=DUR)

# --- BOTTOM row (above every layer — the untouched control) ---
Square(side=2.2, fillColor=rgba(255, 150, 30), strokeColor=TRANSPARENT).position(0, -3).zIndex(20)
