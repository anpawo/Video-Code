#!/usr/bin/env python3


from videocode.shader.ishader import *
from videocode.utils.classutils import Maybe


class translate(VertexShader):
    """
    Shift an `Input`'s position by `(x, y)`, relative to its current position.

    Unlike `position`, this is additive: applying `translate(1, 0)` twice moves
    the input by 2 total, regardless of where it started. Used by `Group.moveTo`/
    `Group.moveBy` so every member shifts by the same delta, preserving their
    relative layout.
    """

    def __init__(self, x: maybe[number] = None, y: maybe[number] = None):
        self.x = x
        self.y = y

    def autodestroy(self, i: Input) -> bool:
        return (self.x is None or self.x == 0) and (self.y is None or self.y == 0)

    def modify(self, i: Input):
        dx = Maybe(self.x) | 0
        dy = Maybe(self.y) | 0
        i.meta.position = v2(i.meta.position.x + dx, i.meta.position.y + dy)
        self.x, self.y = dx, dy
