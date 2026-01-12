#!/usr/bin/env python3


from videocode.videocode import *

# Display the same image three times: left lighter, center original, right darker
img_blur = image("wb.png").position(x=-4, y=0).scale(3).apply(gamma(1.5), duration=2)

img_center = image("wb.png").position(x=0, y=0).scale(3)

img_gamma = image("wb.png").position(x=4, y=0).scale(3).apply(gamma(0.5), duration=2)
