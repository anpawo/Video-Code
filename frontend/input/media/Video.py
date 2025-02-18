#!/usr/bin/env python3


from frontend.input.Input import *


class video(Input):
    def __init__(self, filepath: str) -> None:
        Global.requiredInputs.append(("Video", [filepath]))
