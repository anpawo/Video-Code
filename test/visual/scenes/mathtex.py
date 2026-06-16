#!/usr/bin/env python3

# Visual regression scene — MathTex/Tex (#39).
# Exercises the LaTeX -> dvisvgm -> SVGPath pipeline: fractions, integrals,
# exponents, and fillColor overrides (dvisvgm renders solid black).

from videocode import *

MathTex(r"\frac{1}{2} + \int_0^1 x^2 \, dx", width=4).position(x=0, y=1)
MathTex(r"E = mc^2", fillColor=BLUE_B, width=2).position(x=0, y=-0.5)
MathTex(r"\sqrt{a^2 + b^2}", fillColor=GREEN_A, width=3).position(x=0, y=-2)
