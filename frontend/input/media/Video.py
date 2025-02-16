#!/usr/bin/env python3


from frontend.input._Input import *


class video(Input):
    def __init__(self, filepath: str) -> None:
        Global.variable.append(("Video", [filepath]))
