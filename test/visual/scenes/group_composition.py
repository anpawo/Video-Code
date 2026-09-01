#!/usr/bin/env python3

# Visual regression scene — what a group does to a member that is ALREADY
# animating, and what a group inside a group does.
#
# `groups.py` next door only moves a group whose members are still. That is why
# a measured defect stayed invisible for the whole life of this suite: a group's
# absolute re-emission overwrote a member's own animation on 29 frames out of
# 30, on a plain leaf, with no warning and no scene to catch it.
#
# Three rows, each a case the corpus did not have:
#
#   TOP    — a member TURNING on its own under a group that moves it. Rotation
#            survives because the parent does not claim that channel; position
#            would not, and that asymmetry is measured in
#            `test/group_defect_test.py`, which names it rather than pinning it
#            in a golden.
#   MIDDLE — a group inside a group, both animating. The inner pair must keep
#            turning while the outer one carries them.
#   BOTTOM — a member appended AFTER the group was built. It must move with the
#            others; `Group.apply` used to re-snapshot only when the member list
#            started empty, so an appended member was invisible to every rigid
#            transform and simply sat still.
#
# Frame 0 is the start, frame 15 the middle of every window, frame 29 the end —
# the middle frame is the one that shows a trajectory rather than a destination.

from videocode import *

# ── TOP: member animates, group animates ───────────────────────────────────
turner = Rectangle(width=0.8, height=0.8, fillColor=RED_B, strokeColor=WHITE, strokeWidth=0.04).position(-4, 2.4)
still = Circle(radius=0.4, fillColor=BLUE_B, strokeColor=WHITE, strokeWidth=0.04).position(-2.5, 2.4)
turner.rotateBy(180, duration=1)
Group(turner, still).moveBy(x=5, duration=1)

# ── MIDDLE: a group inside a group, both turning ───────────────────────────
inner = Group(
    Rectangle(width=0.7, height=0.7, fillColor=GREEN_A, strokeColor=WHITE, strokeWidth=0.04).position(-4.4, 0),
    Rectangle(width=0.7, height=0.7, fillColor=YELLOW, strokeColor=WHITE, strokeWidth=0.04).position(-3, 0),
)
inner.rotateBy(180, duration=1)
Group(inner, Circle(radius=0.35, fillColor=BLUE_C, strokeColor=WHITE, strokeWidth=0.04).position(-1.5, 0)).moveBy(x=4, duration=1)

# ── BOTTOM: a member appended after construction ───────────────────────────
built = Group(
    Rectangle(width=0.7, height=0.7, fillColor=GREEN, strokeColor=WHITE, strokeWidth=0.04).position(-4.4, -2.4),
    Rectangle(width=0.7, height=0.7, fillColor=RED_A, strokeColor=WHITE, strokeWidth=0.04).position(-3, -2.4),
)
built.inputs.append(Circle(radius=0.35, fillColor=YELLOW, strokeColor=WHITE, strokeWidth=0.04).position(-1.5, -2.4))
built.moveBy(x=4, duration=1)

wait(1)
