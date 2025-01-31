from python.VideoCode import *

v1 = video("video/v.mp4")

# normal image
v1.add()

# erase top left corner and fade the first half copy
v1.apply(translate(-100, -50))[:30].copy().apply(fadeIn(ALL, -1)).add()

# original
v1.add()
