#!/usr/bin/env python3

# Everything added today, in one scene: `./video-code --file eg.py`

from videocode import *
from videocode.template.effect.other.fillIn import fillIn

# ── the wipe ────────────────────────────────────────────────────────────────
# fillIn sweeps a boundary across the fill. `.fill()` cannot do this: easing
# between two paints interpolates their COLOURS stop by stop, so it can tint
# but never slide an edge. Applied to a Text it travels over the WHOLE WORD —
# that is what `GroupEffect` buys (a letter has no idea where it sits in one).
Text("GRADIENT", fontSize=0.75).position(0, 3).apply(fillIn(LinearGradient(BLUE_C, RED_B), duration=1.6))

# `band` softens the edge, `reverse` sends it the other way, `over` says what
# is being wiped away when it isn't the shape's current fill.
Rectangle(width=5, height=0.5, fillColor=WHITE, strokeColor=TRANSPARENT).position(0, 2).apply(
    fillIn(GREEN_A, band=25, reverse=True, duration=1.6)
)

# ── the morph ───────────────────────────────────────────────────────────────
# A corner count builds a regular polygon of the same AREA, oriented to match
# what is already there. A count the shape has BEEN before is a return: it
# retraces that exact ring instead of fitting a new one, so the square comes
# back where it started rather than tilted.
stars = Square(side=3, cornerRadius=15, fillColor=starNest(scale=0.6)).position(-4.5, -1)
stars.morphTo(6, duration=1.6).wait(0.3).morphTo(4, duration=1.4, easing=Easing.ExponentialDecay)

# ── the math shaders ────────────────────────────────────────────────────────
# `scale` zooms the pattern around `origin`; below 1 everything inside shrinks.
# `origin` picks which part of the pattern the shape shows, in percent of its
# own box — so two shapes side by side can look onto different regions.
Square(side=3, cornerRadius=15, fillColor=starNest(scale=0.25, origin=(20, 20))).position(0, -1)

# evilEye centres itself on its host and follows it. `scale` here is relative
# to the shape's height, so 0.55 fits the whole eye inside the square.
Square(side=3, cornerRadius=15, fillColor=evilEye(scale=0.55, color=rgba("#FF6F37"))).position(4.5, -1)

Text("starNest · morphTo · evilEye", fontSize=0.3, fillColor=WHITE | 0.4).position(0, -3.2)

wait(1)

# ── not shipped yet ─────────────────────────────────────────────────────────
# The council of 2026-07-28 decided `space=`, which is what decides whether a
# pattern is painted ON the shape or merely revealed BY it:
#
#     starNest(space=Space.Shape)    # scaling the host scales the pattern
#     starNest(space=Space.Frame)    # the host is a moving window onto it
#     starNest(space=Space.Anchor)   # frozen where the fill was assigned
#
# See ~/.claude/councils/2026-07-28-videocode-shader-anchor/log.md
