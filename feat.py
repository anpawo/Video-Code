#!/usr/bin/env python3

# One example for every effect and easing in the standard effects pack.
# Render with: ./video-code --file feat.py --generate feat.mp4

from videocode import *
from videocode.template.effect.other.kenBurns import kenBurns
from videocode.template.effect.other.popIn import popIn
from videocode.template.effect.other.pulse import pulse
from videocode.template.effect.other.shake import shake
from videocode.template.effect.other.typewriter import typewriter
from videocode.template.effect.other.wipe import wipeIn, wipeOut

START = 0.6  # everything kicks off together, shortly after the first frame


def label(text: str, x: wnumber, y: wnumber) -> Text:
    return Text(text, fontSize=0.17, fillColor=WHITE | 0.6).position(x, y)


# ── Row 1 (y=3): the three new easings, as falling balls ────────────────────

label("Easing.Back", -6.4, 4.1)
Circle(radius=0.35, fillColor=BLUE_C, strokeColor=WHITE, strokeWidth=0.03) \
    .position(-6.4, 3.4).moveBy(y=-1.8, easing=Easing.Back, start=START, duration=1.4)

label("Easing.Elastic", -3.2, 4.1)
Circle(radius=0.35, fillColor=RED_B, strokeColor=WHITE, strokeWidth=0.03) \
    .position(-3.2, 3.4).moveBy(y=-1.8, easing=Easing.Elastic, start=START, duration=1.4)

label("Easing.Bounce", 0, 4.1)
Circle(radius=0.35, fillColor=GREEN_A, strokeColor=WHITE, strokeWidth=0.03) \
    .position(0, 3.4).moveBy(y=-1.8, easing=Easing.Bounce, start=START, duration=1.4)

label("popIn()", 3.2, 4.1)
Rectangle(width=1.6, height=1.1, fillColor=BLUE_C, strokeColor=WHITE, cornerRadius=15) \
    .position(3.2, 2.9).apply(popIn(start=START, duration=0.6))

label("pulse()", 6.4, 4.1)
Circle(radius=0.55, fillColor=YELLOW, strokeColor=WHITE, strokeWidth=0.03) \
    .position(6.4, 2.9).apply(pulse(scale=1.25, times=2, start=START, duration=1.6))

# ── Row 2 (y=0): motion effects ──────────────────────────────────────────────

label("shake()", -6.4, 1.1)
Rectangle(width=1.6, height=1.1, fillColor=RED_B, strokeColor=WHITE, cornerRadius=15) \
    .position(-6.4, 0).apply(shake(amplitude=0.2, start=START, duration=0.9))

label('wipeIn("left")', -3.2, 1.1)
Rectangle(width=2.4, height=1.1, fillColor=LinearGradient(BLUE_C, GREEN_A), strokeColor=TRANSPARENT) \
    .position(-3.2, 0).apply(wipeIn(direction="left", start=START, duration=1.0))

label('wipeOut("right")', 0, 1.1)
Rectangle(width=2.4, height=1.1, fillColor=LinearGradient(RED_B, YELLOW), strokeColor=TRANSPARENT) \
    .position(0, 0).apply(wipeOut(direction="right", start=START, duration=1.0))

label("kenBurns()", 3.2, 1.1)
Rectangle(width=2.4, height=1.4, fillColor=LinearGradient(BLUE_C, RED_B), strokeColor=TRANSPARENT) \
    .position(3.2, 0).apply(kenBurns(zoom=1.3, panX=-0.4, panY=0.15, start=START, duration=2.8))

label("typewriter()", 6.4, 1.1)
Text("hello", fontSize=0.45, fillColor=WHITE) \
    .position(6.4, 0).apply(typewriter(interval=0.12, fade=0.15, start=START))

# ── Row 3 (y=-3): fragment shaders ───────────────────────────────────────────

FX_LEN = 3.4  # keep the shader visuals up for the whole clip

label("vignette()", -6.4, -1.9)
Rectangle(width=2.6, height=1.7, fillColor=LinearGradient(BLUE_C, RED_B), strokeColor=TRANSPARENT) \
    .position(-6.4, -3).apply(vignette(intensity=0.8, radius=30, smoothness=50), duration=FX_LEN)

label("pixelate()", -3.2, -1.9)
Circle(radius=0.9, fillColor=LinearGradient(GREEN_A, BLUE_C), strokeColor=TRANSPARENT) \
    .position(-3.2, -3).apply(pixelate(22), duration=FX_LEN)

label("glitch()", 0.9, -1.9)
Text("GLITCH", fontSize=0.7, fillColor=WHITE) \
    .position(0.9, -3).apply(glitch(amount=1.2, slices=14, seed=7), duration=FX_LEN)

label("lightSweep()", 5.4, -1.9)
Rectangle(width=2.6, height=1.7, fillColor=BLUE_C, strokeColor=WHITE, cornerRadius=10) \
    .position(5.4, -3).apply(lightSweep(), start=START, duration=1.6)
