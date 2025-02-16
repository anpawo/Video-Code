#!/usr/bin/env python3


from frontend.VideoCode import *


class MyVideo(Scene):
    def scene(self) -> None:
        v1 = video("video/v.mp4")
        v2 = v1.copy()

        v2.apply(translate(50, 50))

        # overlay
        v1.overlay(v2).add()


if __name__ == "__main__":
    MyVideo().scene()
    print(Global())
