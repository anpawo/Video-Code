#!/usr/bin/env python3


from frontend.input.shape._Shape import *


class rectangle(Shape):
    def __init__(self, width: int, height: int) -> None:
        Global.variable.append(("Rectangle", [width, height]))
