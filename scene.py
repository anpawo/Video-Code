#!/usr/bin/env python3

from videocode import *
from videocode.template.effect.other.popIn import popIn

RATIO = 1

square = Square(side=1 * RATIO, cornerRadius=15, fillColor=BLUE_C, strokeColor=WHITE).opacity(0)
circle = Circle(radius=0.5 * RATIO, fillColor=RED_B, strokeColor=WHITE).opacity(0)

square.fadeIn()
square.flush()
square.moveBy(x=-1.5 * RATIO)

circle.waitFor(square)
circle.fadeIn()
circle.flush()
circle.moveBy(x=1.5 * RATIO)

wait(0.3)

g = Group(square, circle).scaleTo(0.5, duration=1.2).rotateBy(180, duration=1.2)

wait(0.5)

g.fadeOut()

wait(1)

marius = Video("marius.mov", width=6, cornerRadius=30).position(x=0, y=0).opacity(0)
marius.scale(2).apply(popIn(duration=0.6))

# arrondi les corners de la video marius de 30%