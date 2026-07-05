#!/usr/bin/env python3

# One example for every effect in batch 3 of the effects pack.
# Render with: ./video-code --file feat.py --generate feat.mp4

from videocode import *
from videocode.template.effect.other.bounceIn import bounceIn
from videocode.template.effect.other.stamp import stamp
from videocode.template.effect.other.swing import swing
from videocode.template.effect.other.tada import tada

START = 0.6
END = 3.6


def label(text: str, x: wnumber, y: wnumber) -> Text:
    return Text(text, fontSize=0.17, fillColor=WHITE | 0.6).position(x, y)


# ── Row 1 (y=2.3): motion templates ──────────────────────────────────────────

label("bounceIn()", -5.4, 3.6)
Circle(radius=0.55, fillColor=BLUE_C, strokeColor=WHITE, strokeWidth=0.04) \
    .position(-5.4, 1.9).apply(bounceIn(height=2.0, start=START, duration=0.9))

label("swing()", -1.8, 3.6)
Rectangle(width=1.8, height=1.2, fillColor=RED_B, strokeColor=WHITE, cornerRadius=15) \
    .position(-1.8, 2.3).apply(swing(angle=20, start=START, duration=1.0))

label("tada()", 1.8, 3.6)
Rectangle(width=1.5, height=1.5, fillColor=GREEN_A, strokeColor=WHITE, cornerRadius=15) \
    .position(1.8, 2.3).apply(tada(start=START, duration=1.0))

label("stamp()", 5.4, 3.6)
Text("APPROVED", fontSize=0.42, fillColor=RED_A) \
    .position(5.4, 2.3).apply(stamp(start=START, duration=0.7))

# ── Row 2 (y=-1.6): filter shaders ───────────────────────────────────────────

label("sepia()", -6.4, -0.4)
Rectangle(width=2.4, height=1.5, fillColor=LinearGradient(BLUE_C, RED_B), strokeColor=TRANSPARENT) \
    .position(-6.4, -1.6).apply(sepia(), duration=END)

label("invert()", -3.2, -0.4)
Rectangle(width=2.4, height=1.5, fillColor=LinearGradient(BLUE_C, RED_B), strokeColor=TRANSPARENT) \
    .position(-3.2, -1.6).apply(invert(), duration=END)

label("hueRotate(120)", 0, -0.4)
Rectangle(width=2.4, height=1.5, fillColor=LinearGradient(BLUE_C, RED_B), strokeColor=TRANSPARENT) \
    .position(0, -1.6).apply(hueRotate(120), duration=END)

label("posterize(4)", 3.2, -0.4)
Rectangle(width=2.4, height=1.5, fillColor=LinearGradient(WHITE, BLACK), strokeColor=TRANSPARENT) \
    .position(3.2, -1.6).apply(posterize(4), duration=END)

label("halftone()", 6.4, -0.4)
Rectangle(width=2.4, height=1.5, fillColor=LinearGradient(WHITE, BLACK), strokeColor=TRANSPARENT) \
    .position(6.4, -1.6).apply(halftone(10), duration=END)
