#!/usr/bin/env python3


from videocode.shader.ishader import *
from videocode.utils.classutils import Maybe


class scaleDelta(VertexShader):
    """
    Shift an `Input`'s scale by `(x, y)`, relative to its current scale.

    Unlike `scale`, this is additive: applying `scaleDelta(0.1, 0)` twice grows
    the input by 0.2 total, regardless of its starting scale. Used by
    `Group.scaleTo`/`Group.scaleBy` so every member grows/shrinks by the same
    delta, preserving their relative scale differences.
    """

    def __init__(self, x: maybe[number] = None, y: maybe[number] = None):
        self.x = x
        self.y = y

    def autodestroy(self, i: Input) -> bool:
        return (self.x is None or self.x == 0) and (self.y is None or self.y == 0)

    def modify(self, i: Input):
        dx = Maybe(self.x) | 0
        dy = Maybe(self.y) | 0
        i.meta.scale = v2(i.meta.scale.x + dx, i.meta.scale.y + dy)
        self.x, self.y = dx, dy
