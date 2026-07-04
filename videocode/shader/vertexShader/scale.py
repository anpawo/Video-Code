#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *
from videocode.utils.classutils import Maybe


class scale(VertexShader):
    _rigidKind = 3
    """
    `Scale` up or down an `Input`'s size.
    """

    def __init__(self, x: maybe[number], y: maybe[number]):
        self.x = x
        self.y = y

    def autodestroy(self, i: Input) -> bool:
        return (i.meta.scale.x is None or i.meta.scale.x == self.x) and (i.meta.scale.y is None or i.meta.scale.y == self.y)

    def modify(self, i: Input):
        i.meta.scale = v2(
            Maybe(self.x) | i.meta.scale.x,
            Maybe(self.y) | i.meta.scale.y,
        )
        self.x, self.y = i.meta.scale
