#!/usr/bin/env python3


from frontend.input._Input import *


class image(Input):
    def __init__(self, filepath: str) -> None:
        Global.variable.append(("Image", [filepath]))
