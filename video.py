from python.VideoCode import *

v1 = video("video/v.mp4")

# normal image
v1.add()

# translated image
v1.apply(translate(100, 50))
v1.add()

# back to normal image
v1.apply(translate(-100, -50))
v1.add()

# erase some parts
v1.apply(translate(-100, -50))
v1.add()
