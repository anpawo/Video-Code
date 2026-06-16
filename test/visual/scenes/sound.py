#!/usr/bin/env python3

# Visual regression scene — Sound (#78).
# A Sound input has no visual geometry (empty mesh) — this verifies it
# doesn't break rendering of the rest of the scene.

from videocode import *

Rectangle(2, 2, fillColor=rgba(255, 0, 0)).position(x=1, y=1)
Sound("test/test.wav", start=1, volume=0.5)
