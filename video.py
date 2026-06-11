#!/usr/bin/env python3


from videocode.template.input._inputs import *
from videocode import *

p = Plane()

# LightSweep showcase — a bright band sweeps across each input's own
# bounding box over the effect's duration (start/duration like any effect).

Text("lightSweep(width, intensity, angle)", fontSize=0.5, fillColor=WHITE).position(y=3)

# A "card" with a shine passing over it, twice.
card = Rectangle(width=6, height=2.5, fillColor=BLUE_C, strokeColor=WHITE, strokeWidth=0.03).position(y=0.8)
card.apply(lightSweep(), duration=1)

# Continuous sweep across the whole word: the broadcast hands the SAME
# lightSweep instance to every letter, so they share a sweep group and the
# band travels across the union of their bounding boxes (metallic-logo style).
t = Text("SHINE", fontSize=1.2, fillColor=GRAY).position(y=-2)
t.apply(lightSweep(width=15), start=1, duration=1.5)
t.apply(lightSweep(width=15), start=3.5, duration=1.5)
