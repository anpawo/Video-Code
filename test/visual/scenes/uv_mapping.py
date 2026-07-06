#!/usr/bin/env python3

# Visual regression scene — textured fill UV mapping modes (#127).
# Three circular Images sharing the same texture: default bbox "stretch",
# "radial" (polar UVs, u=radius/v=angle), and "conic" (u=angle/v=radius).

from videocode import *

Image("wb.png", width=3, height=3, cornerRadius=100, uvMapping=UVMapping.STRETCH).position(x=-3, y=0)
Image("wb.png", width=3, height=3, cornerRadius=100, uvMapping=UVMapping.RADIAL).position(x=0, y=0)
Image("wb.png", width=3, height=3, cornerRadius=100, uvMapping=UVMapping.CONIC, uvAngle=45).position(x=3, y=0)
