#!/usr/bin/env python3


from videocode.shader.ishader import *
from videocode.utils.classutils import Maybe


class align(VertexShader):
    """
    set the alignment of `x` and `y` of an `Input`.

    can be `None` if you only want to change one of the two.
    """

    def __init__(self, x: maybe[number], y: maybe[number]) -> None:
        self.x = x
        self.y = y

    def autodestroy(self, i: Input) -> bool:
        return (i.meta.align.x is None or i.meta.align.x == self.x) and (i.meta.align.y is None or i.meta.align.y == self.y)

    def modify(self, i: Input):
        i.meta.align = v2(
            Maybe(self.x) | i.meta.align.x,
            Maybe(self.y) | i.meta.align.y,
        )
        self.x, self.y = i.meta.align
