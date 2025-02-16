#!/usr/bin/env python3


from frontend.input.shape._Shape import *


class circle(Shape):
    def __init__(self, radius: int) -> None:
        Global.variable.append(("Circle", [radius]))
