#!/usr/bin/env python3


from videocode import *
from videocode.template.input._inputs import *

p = Plane()

# --- Video trimming demo (#92) ---
# `startFrame`/`endFrame` restrict playback to source frames [startFrame, endFrame)
# — here only frames 5..19 of the 24-frame clip play (15 frames), instead of the
# full clip. Equivalent to cuts=[(0, 5), (20, <end>)].
v = Video("test.mp4", startFrame=5, endFrame=20)
