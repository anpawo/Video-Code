#!/usr/bin/env python3

"""F23 — two traps the run must name out loud, on purpose."""

from videocode import *

# Two animations claiming Position:x over the same frames: the later call wins.
fight = Square(side=1, fillColor=BLUE_C, strokeColor=WHITE).position(-3, 1.5)
fight.moveTo(x=2, duration=1)
fight.moveBy(x=1, duration=1)

# A start= that reaches back behind a line written above it.
late = Square(side=1, fillColor=rgba(240, 180, 90), strokeColor=WHITE).position(-3, -1.5)
late.moveTo(x=5, start=2, duration=1)
late.moveTo(x=2, duration=1)

wait(4)
