#!/usr/bin/env python3

# Visual regression scene — effects batch 2 templates (slideIn, slideOut,
# spinIn, zoomPunch, blurIn, flash, jelly). All deterministic. Frames sample
# entrances mid-flight (7), overshoots/dips (15) and the end state (29).

from videocode import *
from videocode.template.effect.other.blurIn import blurIn
from videocode.template.effect.other.flash import flash
from videocode.template.effect.other.jelly import jelly
from videocode.template.effect.other.slide import slideIn, slideOut
from videocode.template.effect.other.spinIn import spinIn
from videocode.template.effect.other.zoomPunch import zoomPunch

Rectangle(width=1.6, height=1.1, fillColor=BLUE_C, strokeColor=WHITE, cornerRadius=15) \
    .position(-4.5, 1.8).apply(slideIn(direction="left", distance=1.5, duration=0.6))

Rectangle(width=1.6, height=1.1, fillColor=RED_B, strokeColor=WHITE, cornerRadius=15) \
    .position(-1.5, 1.8).apply(slideOut(direction="right", distance=1.5, duration=0.8))

Rectangle(width=1.4, height=1.4, fillColor=GREEN_A, strokeColor=WHITE, cornerRadius=15) \
    .position(1.5, 1.8).apply(spinIn(duration=0.8))

Rectangle(width=1.6, height=1.1, fillColor=YELLOW, strokeColor=WHITE, cornerRadius=15) \
    .position(4.5, 1.8).apply(zoomPunch(duration=0.7))

Text("BLUR", fontSize=0.6, fillColor=WHITE) \
    .position(-3.0, -1.8).apply(blurIn(strength=21, duration=0.8))

Rectangle(width=1.6, height=1.1, fillColor=LinearGradient(BLUE_C, RED_B), strokeColor=TRANSPARENT) \
    .position(0.0, -1.8).apply(flash(amount=160, duration=0.8))

# duration=1.0 keeps the scene alive through frame 29 (the last sampled
# golden frame) — a shorter longest-effect makes frame 29 not exist at all.
Circle(radius=0.8, fillColor=GREEN_A, strokeColor=WHITE, strokeWidth=0.04) \
    .position(3.0, -1.8).apply(jelly(amplitude=0.25, duration=1.0))
