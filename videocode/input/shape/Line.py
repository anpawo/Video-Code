#!/usr/bin/env python3


from videocode.input.shape._Shape import *


class line(Shape):
    def __init__(self, length: int) -> None:
        Global.requiredInputs.append(("Line", [length]))
