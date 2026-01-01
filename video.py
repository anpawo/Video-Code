#!/usr/bin/env python3


# from videocode.template.input.numberLine import numberLine
from videocode.videocode import *

# TODO: grid test
# g = numberLine()

# TODO: circle test
# r1 = rectangle(width=3).align(y=0, x=0)
# r2 = rectangle(width=3, color=RED).align(y=0.5, x=0.5).apply(grayscale(), start=SF * 2, duration=SF * 10)

# for i in range(13):
#     r1.width += 0.1
#     r1.rotate(90 / 12 * i)
#     r2.rotate(90 / 12 * i)

#     r1.flush()
#     r2.flush()

# r1.apply(fadeOut())

# TODO: group test
s = square().position(x=-2).scale(0).scaleTo(1).fadeIn().flush()
# wait(0.5)
s.moveBy(x=2).flush()
# wait(0.5)
s.fadeOut().scaleTo(2)
