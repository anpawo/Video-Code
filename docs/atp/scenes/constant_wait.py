#!/usr/bin/env python3

"""F22 — the pauses are a NAMED constant, read by three lines."""

from videocode import *

PAUSE_DELAY = 0.6

r = Rectangle(width=2, height=1.2, fillColor=BLUE_C, strokeColor=WHITE).fadeIn(duration=0.4)
wait(PAUSE_DELAY)
r.moveTo(x=2.5, duration=0.8)
wait(PAUSE_DELAY)
r.fadeOut(duration=0.4)
wait(PAUSE_DELAY)
