#!/usr/bin/env python3

from videocode import *

# One number for the whole scene. Every size and every distance below is a
# multiple of it, so making the whole thing bigger — or smaller — is a single
# edit rather than six. `cornerRadius` is deliberately NOT multiplied: it is a
# percentage of the shape's own side, so it already grows with it.
RATIO = 1

square = Square(side=1 * RATIO, cornerRadius=15, fillColor=BLUE_C, strokeColor=WHITE).opacity(0)
circle = Circle(radius=0.5 * RATIO, fillColor=RED_B, strokeColor=WHITE).opacity(0)

# The square appears in the middle, then steps left. `flush()` between the two
# is what makes them a sequence: without it both would start at the element's
# own cursor and play at once. It moves that cursor to the end of what has been
# scheduled, and it says only that — a `wait(0)` would be the same thing spelled
# as a pause of no length.
square.fadeIn()
square.flush()
square.moveBy(x=-1.5 * RATIO)

# The circle waits for the square to be done, then does the same to the right.
circle.waitFor(square)
circle.fadeIn()
circle.flush()
circle.moveBy(x=1.5 * RATIO)

wait(0.3)

# Turning and shrinking together: one group, two animations of the same length.
Group(square, circle).scaleTo(0.5, duration=1.2).rotateBy(180, duration=1.2)

wait(0.5)

# ── Two faults to uncomment, to see what the editor says about them ──────────
#
# A WARNING. The scene still runs; the two lines fight over the same channel on
# the same frames, and the later one wins them. Orange in the code, orange on
# the element in the timeline.
# square.moveBy(x=1, duration=1)
# square.moveBy(x=-1, duration=1)
#
# An ERROR. The scene does not run at all: the message lands on the line, and
# the picture keeps the last frame that worked rather than going blank.
# Circle(radius=-1)
