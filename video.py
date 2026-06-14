#!/usr/bin/env python3


from videocode import *
from videocode.template.input._inputs import *

p = Plane()


# --- SVG input (#75) ---
SVG("icon.svg", width=2, height=2).position(x=-1, y=2.5)

# --- Subtitles (#79) ---
Subtitles("test/test.srt")

# --- Markdown (#76) ---
Markdown("test/test.md")

# --- Sound (#78) ---
Sound("test/test.wav", start=1, volume=0.5)
