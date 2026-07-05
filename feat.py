#!/usr/bin/env python3

# One example for every effect in batch 4 (Tier 1 compositing gap) of the
# effects pack: chromaKey + the crossfade/push/wipeBetween transitions API.
# Render with: ./video-code --file feat.py --generate feat.mp4

from videocode import *
from videocode.template.effect.other.transitions import crossfade, push, wipeBetween


def label(text: str, x: wnumber, y: wnumber) -> Text:
    return Text(text, fontSize=0.17, fillColor=WHITE | 0.6).position(x, y)


# ── chromaKey(): green background keyed out, red circle behind shows through ─

label("chromaKey()", -6.4, 2.2)
Circle(radius=1.1, fillColor=RED_B, strokeColor=TRANSPARENT).position(-6.4, 0.6)
Rectangle(width=2.4, height=2.4, fillColor=GREEN, strokeColor=TRANSPARENT) \
    .position(-6.4, 0.6).apply(chromaKey(color=GREEN, tolerance=0.35, softness=0.1), duration=3.4)

# ── crossfade(): blue dissolves into red ────────────────────────────────────

label("crossfade()", -2.5, 2.2)
cfOut = Rectangle(width=1.8, height=1.8, fillColor=BLUE_C, strokeColor=TRANSPARENT).position(-2.5, 0.6)
cfIn = Rectangle(width=1.8, height=1.8, fillColor=RED_B, strokeColor=TRANSPARENT).position(-2.5, 0.6).opacity(0).hide()
crossfade(cfOut, cfIn, start=0.6, duration=0.8)

# ── push(): green pushed out to the left, yellow enters from the right ─────

label('push("left")', 1.4, 2.2)
pOut = Rectangle(width=1.8, height=1.8, fillColor=GREEN_A, strokeColor=TRANSPARENT).position(1.4, 0.6)
pIn = Rectangle(width=1.8, height=1.8, fillColor=YELLOW, strokeColor=TRANSPARENT).position(1.4, 0.6).hide()
push(pOut, pIn, direction="left", distance=2.2, start=0.6, duration=0.7)

# ── wipeBetween(): gradient wiped away to reveal another gradient ──────────

label('wipeBetween("left")', 5.4, 2.2)
wOut = Rectangle(width=2.2, height=1.8, fillColor=LinearGradient(RED_B, BLUE_C), strokeColor=TRANSPARENT).position(5.4, 0.6)
wIn = Rectangle(width=2.2, height=1.8, fillColor=LinearGradient(GREEN_A, YELLOW), strokeColor=TRANSPARENT).position(5.4, 0.6).hide()
wipeBetween(wOut, wIn, direction="left", start=0.6, duration=0.8)
