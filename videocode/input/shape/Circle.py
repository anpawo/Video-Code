#!/usr/bin/env python3


from videocode.input.shape._Shape import *


class circle(Shape):
    def __init__(self, radius: int) -> None:
        Global.requiredInputs.append(("Circle", [radius]))
