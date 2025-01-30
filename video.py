from python.VideoCode import *

v1 = video("video/v.mp4")

v1.apply(
    fadeIn(LEFT, -1),
    fadeIn(RIGHT, -1),
    fadeIn(UP, -1),
    fadeIn(DOWN, -1),
)
v1.add()
