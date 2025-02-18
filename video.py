#!/usr/bin/env python3


from frontend.VideoCode import *


# import the video
v1 = video("video/v.mp4")
v2 = v1.copy()

# translation
v2.apply(
    translate(50, 50),
)

# overlay
v1.apply(
    overlay(v2),
)

# add
v1.add()


if __name__ == "__main__":
    print(Global())

# TODO: remove the scene, the code can be in nothing
