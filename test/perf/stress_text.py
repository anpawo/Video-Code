#!/usr/bin/env python3

# Performance benchmark scene — animated text, the historical hot path.
# 3 Texts = ~47 letter Polygon inputs, animated over 300 frames
# (~13,800 Apply entries). Used by test/perf/bench.py; do not change the
# content without re-recording the baseline in docs/optimization.md.

from videocode import *

t1 = Text("The quick brown fox", fontSize=0.5, fillColor=WHITE).position(y=1.5)
t2 = Text("jumps over the lazy dog", fontSize=0.5, fillColor=RED_B).position(y=0)
t3 = Text("0123456789!?", fontSize=0.5, fillColor=BLUE_B).position(y=-1.5)

t1.moveTo(x=2, start=0, duration=10)
t2.moveTo(x=-2, start=0, duration=10)
t3.moveTo(y=-0.5, start=0, duration=10)
