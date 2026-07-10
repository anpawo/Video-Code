#!/usr/bin/env python3

# feat.py shows ONE example for the newest feature only (project convention).
#
# Newest: SHADER FILLS — `fillColor=<shader>` on any shape or Text. The
# shader is persistent fill state: it paints every frame from creation until
# fillColor is reassigned (to a color or another shader) or the video ends.
# Hiding/fading does NOT end it — the fill is back when the input is.
#
#   0.0s  FIRE fades in, burning
#   1.6s  FIRE fades out...
#   3.2s  ...and fades back in — still burning (persistence)
#   4.4s  FIRE drifts upward while burning
#   4.5s  the bottom line switches fire -> plain white ("until changed")
#
# Preview: ./video-code --file feat.py

from videocode import *

BG = rgba(12, 10, 14)

title = Text("FIRE", fontSize=2.6, fillColor=fire(speed=2)).position(0, 1.2)
title.fadeIn(duration=0.8)
title.wait(0.8).fadeOut(duration=0.8)
title.wait(0.8).fadeIn(duration=0.8)
title.wait(0.4).moveBy(y=0.7, duration=1.2)

switch = Text("UNTIL CHANGED", fontSize=0.9, fillColor=fire()).position(0, -1.8)
switch.waitTo(int(4.5 * FRAMERATE))
switch.fillColor = WHITE

Text("fillColor=fire()  —  the shader IS the fill: persistent until changed", fontSize=0.18, fillColor=WHITE | 0.7).position(0, -3.6)

# wait() is a scheduling gap, not a freeze — the flames keep burning through
# it. (freeze(n) is the literal freeze-frame if you ever want one.)
wait(7)
