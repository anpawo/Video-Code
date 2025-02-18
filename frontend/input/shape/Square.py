#!/usr/bin/env python3


from frontend.input.shape._Shape import *


class square(Shape):
    def __init__(self, side: int) -> None:
        Global.requiredInputs.append(("Square", [side]))
