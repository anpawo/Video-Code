#!/usr/bin/env python3


# from videocode.template.input.numberLine import numberLine
from videocode.videocode import *

# TODO: grid test
# g = numberLine()

# TODO: animate test
s = square().position(x=-2).scale(0).scaleTo(1).fadeIn().flush()
s.moveBy(x=2).flush()
s.fadeOut().scaleTo(2)
