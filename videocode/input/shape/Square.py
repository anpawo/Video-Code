#!/usr/bin/env python3


from videocode.input.shape._Shape import *


class square(Shape):
    def __init__(self, side: int) -> None:
        Global.stack.append(("Square", [side]))
