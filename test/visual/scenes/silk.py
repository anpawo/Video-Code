#!/usr/bin/env python3

# Visual regression scene — silk procedural "math shader" + track matte.
#
# Top: silk applied to a plain rectangle — the generated raymarched pattern
# must fill the rect (a broken port shows solid black, solid white, or the
# rect's own fill color instead of colorful turbulence; wrong alpha handling
# shows a hard rectangle of noise bleeding outside rounded corners).
#
# Bottom: the flagship composition — silk poured through text via .matte():
# the pattern must appear ONLY inside the glyphs (a broken matte shows the
# full rect; broken alpha shows solid glyphs of one color).
#
# Frame 0 is deterministic: elapsed = 0 → T = 0, the pattern's initial state.

from videocode import *
from videocode.template.input.CompoundPolygon import CompoundPolygon

# Plain rectangle host — pattern fills it, rounded corners must stay clean.
Rectangle(width=10, height=2.6, fillColor=silk(), strokeColor=TRANSPARENT, cornerRadius=25).position(0, 2.2)

# Matted through a word (single input via CompoundPolygon, as .matte() requires).
with Context.noRegister():
    letters = Text("SILK", fontSize=2.2, fillColor=WHITE).inputs
word = CompoundPolygon(*letters).position(0, -1.6)
Rectangle(width=11, height=3.2, fillColor=silk(), strokeColor=TRANSPARENT).position(0, -1.6).matte(word)

# A pure-state scene schedules nothing — extend the timeline so frame 15
# exists. wait() is a scheduling gap, not a freeze: the paint keeps flowing.
wait(1)
