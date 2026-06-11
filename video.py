#!/usr/bin/env python3


from videocode.template.input._inputs import *
from videocode.template.misc.chess.chessboard import ChessBoard
from videocode.template.misc.example.marius import *
from videocode import *

p = Plane()

t = Text("Bonjour", fillColor=LinearGradient(RED, BLUE), fontSize=1)
gradA = LinearGradient(RED, BLUE)
gradB = LinearGradient(GREEN, RED)
for _ in range(5):
    for k in Easing.InOut.range(0, 1, 0.75):
        t.fillColor = gradA + (gradB - gradA) * k
        t.flush()
    for k in Easing.InOut.range(0, 1, 0.75):
        t.fillColor = gradB + (gradA - gradB) * k
        t.flush()
