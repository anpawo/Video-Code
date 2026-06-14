#!/usr/bin/env python3

# Visual regression scene — SVG input (#75).
# icon.svg contains a filled rect, a stroked (unfilled) circle, and a
# fill-rule=evenodd path with a hole — exercises fill, stroke, and
# earcut-with-holes on parsed SVG geometry.

from videocode import *

SVG("icon.svg").position(x=-2, y=1)
SVG("icon.svg", width=3, height=1.5).position(x=-1.5, y=-2)
