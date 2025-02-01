from python.VideoCode import *

v1 = video("video/v.mp4")[0]
v2 = v1.copy()

v2.apply(translate(50, 50))

# v1 frame
v1.add()

# overlay
v1.overlay(v2).add()
