#!/usr/bin/env python3


from frontend.VideoCode import *


# import the video
v1 = video("video/v.mp4").apply(fade(LEFT)).add().apply(translate(50, 50)).add()


if __name__ == "__main__":
    print(Global())
