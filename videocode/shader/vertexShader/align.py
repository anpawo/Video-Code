#!/usr/bin/env python3


from videocode.shader.ishader import *


class align(VertexShader):
    """
    set the alignment of `x` and `y` of an `Input`.

    can be `None` if you only want to change one of the two.
    """

    def __init__(self, x: maybe[number], y: maybe[number]) -> None:
        self.x = x
        self.y = y

    def modificator(self, i: Input):
        if self.x is None:
            self.x = i.meta.align.x
        if self.y is None:
            self.y = i.meta.align.y

        i.meta.align = v2(self.x, self.y)
