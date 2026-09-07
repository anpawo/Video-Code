#!/usr/bin/env python3

"""F9 — move, scale and rotate, each one a line."""

from videocode import *

s = Square(side=1.2, fillColor=BLUE_C, strokeColor=WHITE).position(-4, 0)
s.moveTo(x=4, duration=1.2, easing=Easing.InOut)
s.scaleTo(2, start=1.2, duration=0.8)
s.rotateTo(135, start=2.0, duration=1.0, easing=Easing.InOut)
s.moveTo(y=1.5, start=3.0, duration=0.8)

Text(text="moveTo · scaleTo · rotateTo", fontSize=0.32, fillColor=rgba(150, 156, 170)).position(0, -3)
wait(4)
