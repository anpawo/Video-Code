#!/usr/bin/env python3


from frontend.VideoCode import *


class MyVideo(Scene):
    def scene(self) -> None:
        v1 = video("video/v.mp4")
        v2 = v1.copy()

        print(v1.index)
        print(v2.index)

        v2.apply(translate(50, 50))

        # overlay
        v1.overlay(v2).add()


print(Global())
MyVideo().scene()
print(Global())
