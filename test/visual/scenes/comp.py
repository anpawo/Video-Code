# Visual regression scene — comps (a group that renders as ONE layer).
#
# Three rows, each a side-by-side "without / with", so a broken flatten fails
# obviously:
#
#   TOP     two overlapping white squares at 50%. LEFT is a plain Group: each
#           member fades on its own, so the overlap is a bright band. RIGHT is
#           a Composition: one flat 50% shape, no band. That band is the whole point —
#           if both sides look the same, the comp is not flattening.
#   MIDDLE  two TOUCHING opaque squares under a blur. LEFT is a Group: the
#           blur runs per member, so each square blurs its own inner edge and a
#           dark seam opens between them. RIGHT is a Compositionosition: the pair is one
#           shape by the time the blur runs, so the join is solid.
#   BOTTOM  a rainbow rectangle clipped to the word "COMP" — the matte source
#           is a Composition of the letters, no CompoundPolygon flattening by hand.
#
# So a correct render shows: a seam on the left of the top two rows and none on
# the right, and rainbow letters spelling COMP. Eyeball the golden.

from videocode import *

WHITE_SQ = dict(side=2, fillColor=WHITE, strokeColor=TRANSPARENT)

# --- TOP: the group fade, without and with ---
Group(
    Square(**WHITE_SQ).position(-6, 3),
    Square(**WHITE_SQ).position(-4.6, 3),
).opacity(128)

Composition(
    Square(**WHITE_SQ).position(4.6, 3),
    Square(**WHITE_SQ).position(6, 3),
).opacity(128)

# --- MIDDLE: an effect over the pair, without and with. The squares TOUCH,
# so a per-member blur has an inner edge to eat and a comp-level one does not.
ORANGE = rgba(255, 140, 40)
Group(
    Square(side=2, fillColor=ORANGE, strokeColor=TRANSPARENT).position(-6, 0),
    Square(side=2, fillColor=ORANGE, strokeColor=TRANSPARENT).position(-4, 0),
).apply(blur(strength=3.0), duration=1)

Composition(
    Square(side=2, fillColor=ORANGE, strokeColor=TRANSPARENT).position(4, 0),
    Square(side=2, fillColor=ORANGE, strokeColor=TRANSPARENT).position(6, 0),
).apply(blur(strength=3.0), duration=1)

# --- BOTTOM: a Comp as a matte source — a multi-letter Text is one input now ---
RAINBOW = LinearGradient(
    rgba(255, 60, 60),
    rgba(255, 200, 40),
    rgba(60, 220, 120),
    rgba(60, 160, 255),
    rgba(200, 80, 255),
)
word = Composition(*Text("COMP", fontSize=2.0, fillColor=WHITE).position(0, -3).inputs)
Rectangle(width=10, height=2.6, fillColor=RAINBOW, strokeColor=TRANSPARENT) \
    .position(0, -3) \
    .matte(word)
