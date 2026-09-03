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

# Two lines claiming x over the same frames. The later one wins them, and the
# editor says so in orange — on the line, on the element in the timeline, and on
# the call in its effect tree. Comment them out for a clean scene.
square.moveBy(x=1, duration=1)
square.moveBy(x=-1, duration=1)

# And a fault that stops the scene running at all. Uncomment it to watch the
# picture keep the last frame that worked while the message lands on the line.
# Circle(radius=-1)
