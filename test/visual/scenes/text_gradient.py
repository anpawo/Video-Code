#!/usr/bin/env python3

# Visual regression scene — Text fillColor/strokeColor LinearGradient.
# Exercises per-letter gradient slicing (background-clip: text) for a
# static fillColor + strokeColor gradient, plus an animated fillColor
# gradient that lerps between two LinearGradients via gradient-to-gradient
# arithmetic: gradA + (gradB - gradA) * k.

from videocode import *

# Static gradient fill + stroke spanning the whole word.
Text("Bonjour", fontSize=0.6, fillColor=LinearGradient(RED, BLUE), strokeColor=LinearGradient(BLUE, GREEN), strokeWidth=0.02).position(y=1.3)

# Animated fillColor gradient — lerps gradA -> gradB -> gradA frame by frame.
t = Text("Bonjour", fillColor=LinearGradient(RED, BLUE), fontSize=1).position(y=-1)
gradA = LinearGradient(RED, BLUE)
gradB = LinearGradient(GREEN, RED)
for k in Easing.InOut.range(0, 1, 0.75):
    t.fillColor = gradA + (gradB - gradA) * k
    t.flush()
for k in Easing.InOut.range(0, 1, 0.75):
    t.fillColor = gradB + (gradA - gradB) * k
    t.flush()
