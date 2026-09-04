#!/usr/bin/env python3

"""
The first scene: one rectangle fades in, then holds for a second.

Render it:      ./video-code --file docs/by-example/firstRectangle.py --generate first.mp4
Edit it live:   ./video-code --file docs/by-example/firstRectangle.py --editor
"""

from videocode import *

Rectangle(width=3, height=2, fillColor=BLUE_C, strokeColor=WHITE).fadeIn()

wait(1)
