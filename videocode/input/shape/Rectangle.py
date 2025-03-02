#!/usr/bin/env python3


from videocode.input.shape._Shape import *


class rectangle(Shape):
    def __init__(self, width: int, height: int) -> None:
        Global.requiredInputs.append(("Rectangle", [width, height]))
