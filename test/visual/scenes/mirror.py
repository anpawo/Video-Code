#!/usr/bin/env python3

# Visual regression scene — Input.mirror()/Group.mirror() replicating shaders
# onto linked targets.
#
# Top pair: rotateBy/scaleBy resolve to an absolute destination before
# apply() runs, so the mirrored target ends up at the SAME resulting
# rotation/scale as the source, even though it stays at its own position.
#
# Bottom pair: Group.moveBy uses an additive `translate` shader, so the
# mirrored target keeps its own position and shifts by the same delta —
# relative offsets between leader and follower are preserved.

from videocode import *
from videocode.input.interface.Group import Group

p = Plane()

leader = Rectangle(fillColor=BLUE_C | BLACK).position(x=-4, y=2)
follower = Rectangle(fillColor=RED | BLACK).position(x=4, y=2)
leader.mirror(follower)

leader.rotateBy(45, duration=1, start=0)
leader.scaleBy(1.4, duration=1, start=1)

leaderG = Rectangle(fillColor=GREEN | BLACK).position(x=-4, y=-2.5)
followerG = Rectangle(fillColor=BLUE_A | BLACK).position(x=4, y=-2.5)
group = Group(leaderG)
group.mirror(followerG)

group.moveBy(x=3, duration=1, start=0)
group.moveBy(x=-6, duration=1, start=1)
