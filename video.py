#!/usr/bin/env python3


from videocode import *
from videocode.template.input._inputs import *

p = Plane()


# --- SVG input (#75) ---
SVG("icon.svg", width=2, height=2).position(x=-1, y=2.5)

# --- Subtitles (#79) ---
Subtitles("test/test.srt")
