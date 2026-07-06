#!/usr/bin/env python3

# Visual regression scene — editor-style effect templates (popIn, pulse,
# shake, typewriter, wipeIn, wipeOut, kenBurns). All deterministic: shake is
# a pure sine, typewriter a fixed stagger. Frames sample entrances mid-flight
# (7), settled overshoots (15) and the end state (29).

from videocode import *
from videocode.template.effect.other.kenBurns import kenBurns
from videocode.template.effect.other.popIn import popIn
from videocode.template.effect.other.pulse import pulse
from videocode.template.effect.other.shake import shake
from videocode.template.effect.other.typewriter import typewriter
from videocode.template.effect.other.wipe import wipeIn, wipeOut

Rectangle(width=1.6, height=1.1, fillColor=BLUE_C, strokeColor=WHITE, cornerRadius=15) \
    .position(x=-4.5, y=1.8).apply(popIn(duration=0.5))

Circle(radius=0.7, fillColor=RED_B, strokeColor=WHITE) \
    .position(x=-1.5, y=1.8).apply(pulse(scale=1.3, duration=0.9))

Rectangle(width=1.6, height=1.1, fillColor=GREEN_A, strokeColor=WHITE, cornerRadius=15) \
    .position(x=1.5, y=1.8).apply(shake(amplitude=0.25, duration=0.9))

Rectangle(width=1.6, height=1.1, fillColor=YELLOW, strokeColor=WHITE, cornerRadius=15) \
    .position(x=4.5, y=1.8).apply(kenBurns(zoom=1.5, panX=-0.6, duration=1.0))

Text("TYPEWRITER", fontSize=0.55, fillColor=WHITE).position(y=-0.4) \
    .apply(typewriter(interval=0.08))

Rectangle(width=3.2, height=1.2, fillColor=LinearGradient(BLUE_C, GREEN_A), strokeColor=TRANSPARENT) \
    .position(x=-2.5, y=-2.2).apply(wipeIn(direction=Direction.LEFT, duration=0.8))

Rectangle(width=3.2, height=1.2, fillColor=LinearGradient(RED_B, YELLOW), strokeColor=TRANSPARENT) \
    .position(x=2.5, y=-2.2).apply(wipeOut(direction=Direction.RIGHT, duration=0.8))
