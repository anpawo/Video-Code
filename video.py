#!/usr/bin/env python3


# from videocode.template.input.numberLine import numberLine
from videocode.VideoCode import *

# Display the same image three times: left grain, center original, right brightness.
img_grain = image("hehe.jpg").position(x=-600, y=0).scale(3)
img_grain.apply(grain(0.10), duration=2)

img_center = image("hehe.jpg").position(x=0, y=0).scale(3)

img_brightness = image("hehe.jpg").position(x=600, y=0).scale(3)
img_brightness.apply(brightness(-100), duration=2)
