#!/usr/bin/env python3

# Visual regression scene — percent stop positioning in multi-stop gradients.
# Uses high-contrast BLACK/WHITE stops so the exact pixel position of each stop
# is visually unambiguous (bright band is clearly left/center/right of the shape).

from videocode import *

# White peak at 25% (bright band clearly left of center)
Rectangle(width=3, height=1.4, fillColor=LinearGradient(BLACK, (WHITE, 25), BLACK), strokeColor=TRANSPARENT).position(x=-4.5, y=2.5)

# White peak at 50% (bright band exactly centered, symmetric halves)
Rectangle(width=3, height=1.4, fillColor=LinearGradient(BLACK, (WHITE, 50), BLACK), strokeColor=TRANSPARENT).position(x=0, y=2.5)

# White peak at 75% (bright band clearly right of center)
Rectangle(width=3, height=1.4, fillColor=LinearGradient(BLACK, (WHITE, 75), BLACK), strokeColor=TRANSPARENT).position(x=4.5, y=2.5)

# Two pinned stops: dark → bright@30% → dark@70% → bright (two distinct bright bands)
Rectangle(width=3, height=1.4, fillColor=LinearGradient(BLACK, (WHITE, 30), (BLACK, 70), WHITE), strokeColor=TRANSPARENT).position(x=-4.5, y=0.5)

# Auto-distribution: 4 stops, none pinned → evenly spaced at 0%, 33%, 67%, 100%
# Alternating pattern: the two white bands should appear at the 1/3 and 2/3 marks
Rectangle(width=3, height=1.4, fillColor=LinearGradient(BLACK, WHITE, BLACK, WHITE), strokeColor=TRANSPARENT).position(x=0, y=0.5)

# Near-edge stop: dark band at 10% (very narrow dark notch near left edge)
Rectangle(width=3, height=1.4, fillColor=LinearGradient(WHITE, (BLACK, 10), WHITE), strokeColor=TRANSPARENT).position(x=4.5, y=0.5)

# Percent + angle: white peak at 25% along 90° axis (bright zone in top quarter)
Rectangle(width=3, height=1.4, fillColor=LinearGradient(BLACK, (WHITE, 25), BLACK, angle=90), strokeColor=TRANSPARENT).position(x=-4.5, y=-1.5)

# 4-stop with mixed pinned/auto: RED → GREEN@50% → BLUE_B@75% → WHITE
# Same as main gradient scene but serves as a stable percent reference
Rectangle(width=3, height=1.4, fillColor=LinearGradient(RED, (GREEN_A, 50), (BLUE_B, 75), WHITE), strokeColor=TRANSPARENT).position(x=0, y=-1.5)

# Clustered stops: two stops near each other at 45%/55% → narrow white zone at center
Rectangle(width=3, height=1.4, fillColor=LinearGradient(BLACK, (WHITE, 45), (WHITE, 55), BLACK), strokeColor=TRANSPARENT).position(x=4.5, y=-1.5)
