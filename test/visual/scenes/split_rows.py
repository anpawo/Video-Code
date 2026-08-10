#!/usr/bin/env python3

# Visual regression scene — `SplitView` stacking itself in a portrait frame.
#
# The scene never names an orientation: `Split.AUTO` reads the world box, and
# the suite renders this case at 1080x1920, so it lays the panels out as ROWS.
# The same source at the default 16x9 produces COLUMNS — that is the property
# being pinned, and it is what lets one scene render to both a landscape and a
# phone-shaped master with nothing but a --width/--height change.
#
# Content is placed only through `sv.a` / `sv.b`, exactly as `video.py` and
# `docs/by-example/tuto.py` do: if stacking ever stopped answering those the
# same way, the text here would leave its panel.

from videocode import *
from videocode.template.input._inputs import *

BG = rgba(18, 20, 32)

sv = SplitView(ratio=3 / 5)

# Corner-anchored, so a panel that moved or resized shifts these visibly.
Text("A", fontSize=0.8).align(x=0, y=1).position(sv.a.left, sv.a.top)
Text("a.bot", fontSize=0.5, fillColor=BLUE_A).align(x=1, y=0).position(sv.a.right, sv.a.bot)
Circle(radius=0.5, fillColor=RED_A, strokeColor=TRANSPARENT).position(sv.a.cx, sv.a.cy)

Text("B", fontSize=0.8).align(x=0, y=1).position(sv.b.left, sv.b.top)
Rectangle(
    width=sv.b.innerWidth, height=0.3, fillColor=GREEN_A, strokeColor=TRANSPARENT
).position(sv.b.cx, sv.b.cy)
