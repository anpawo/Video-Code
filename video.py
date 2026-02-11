#!/usr/bin/env python3


from videocode.videocode import *

# Display the same image three times: left light sharpen, center original, right strong sharpen
img_soft_sharpen = image("../test.png").position(x=-4, y=0).scale(0.5).apply(blur(300), duration=2)

img_center = image("../test.png").position(x=0, y=0).scale(0.5)

img_strong_sharpen = image("../test.png").position(x=4, y=0).scale(0.5).apply(brightness(-50.0), duration=2)
