#!/usr/bin/env python3


# from videocode.template.input.numberLine import numberLine
from videocode.VideoCode import *

# Display the same image three times: left sharpen strong, center original, right sharpen soft.
img_sharp_strong = image("hehe.jpg").position(x=-600, y=0).scale(3)
img_sharp_strong.apply(sharpen(5.0), duration=2)

img_center = image("hehe.jpg").position(x=0, y=0).scale(3)

img_sharp_soft = image("hehe.jpg").position(x=600, y=0).scale(3)
img_sharp_soft.apply(sharpen(5.0), duration=2)
