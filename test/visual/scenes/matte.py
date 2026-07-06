#!/usr/bin/env python3

# Visual regression scene — track matte / mask (A.matte(B): A visible only
# where B has coverage).
#
# Flagship use case: a big colorful "content" fill clipped to a TEXT silhouette.
# The content is a vivid multi-stop LinearGradient rectangle (stand-in for a
# Video/Image — a large colorful layer); the matte is the word "MATTE" merged
# into a SINGLE input via CompoundPolygon (a multi-letter Text is a Group of
# Letters with no single index, and the matte source must be one input).
#
# A WORKING matte shows rainbow-filled letters shaped like "MATTE" and nothing
# else — the source text is consumed purely as a mask, never drawn. A BROKEN
# matte fails obviously: the full gradient rectangle (no text shape), a blank
# frame, or the plain white text. So eyeball the golden, don't trust the run.

from videocode import *
from videocode.template.input.CompoundPolygon import CompoundPolygon

RAINBOW = LinearGradient(
    rgba(255, 60, 60),
    rgba(255, 200, 40),
    rgba(60, 220, 120),
    rgba(60, 160, 255),
    rgba(200, 80, 255),
)

# Matte source B — "MATTE" as one input. Built in noRegister so the letters are
# not registered individually; CompoundPolygon unions their contours.
with Context.noRegister():
    letters = Text("MATTE", fontSize=2.4, fillColor=WHITE).inputs
word = CompoundPolygon(*letters).position(0, 0)

# Content A — a large rainbow gradient that fully covers the word, clipped to
# the word's silhouette. B is consumed as a mask and never drawn on its own.
Rectangle(width=12, height=3.2, fillColor=RAINBOW, strokeColor=TRANSPARENT) \
    .position(0, 0) \
    .matte(word)
