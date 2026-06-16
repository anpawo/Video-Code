#!/usr/bin/env python3

# Performance benchmark scene — text morphing, the "Args" VertexShader hot path.
# A single Letter whose `char` changes every frame for 300 frames. Each change
# triggers Polygon.updatePoints -> args("points"/"contourSizes", ...) -> the Args
# VertexShader -> Metadata.pointsPtr/contourSizesPtr (typed COW fields, no JSON clone)
# -> Polygon::buildPath. Regression scene for that fast path.

from videocode import *

t = Text("0", fontSize=1, fillColor=WHITE)

for i in range(300):
    t.text = str(i % 10)
    wait(1)
