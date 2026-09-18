#!/usr/bin/env python3

from videocode import *

PAUSE = 0.5

title = Text("Hello").fadeIn()
square = Square(side=1, fillColor=BLUE_C).opacity(0)
square.wait(1).fadeIn()
square.hide(start=1.5)
circle = Circle(radius=0.5, fillColor=RED_B).wait(PAUSE).fadeIn()
still = Rectangle(width=1, height=1).position(x=3)
dropped = Square(side=0.5).position(x=-3)
dropped.hide()
dropped.show(start=1)
early = Circle(radius=0.3).position(y=2).opacity(0)

wait(2)

early.fadeIn()
late = Square(side=0.4).position(y=-2).wait(0.5).fadeIn()
