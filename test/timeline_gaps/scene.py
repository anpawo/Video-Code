#!/usr/bin/env python3

from videocode import *

GAP = 0.5

box = Rectangle(width=3, height=2, fillColor=BLUE_C, strokeColor=WHITE).position(-3, 0).fadeIn()
wait(1)
disc = Circle(radius=1, fillColor=RED).position(3, 0).fadeIn()
wait(0.3)
label = Text(text="hello").position(0, 2.5).fadeIn()
wait(GAP)
box.hide()
wait(1.2)
wait(0.8)
