#!/usr/bin/env python3

from __future__ import annotations

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
        # Claiming nothing at all is a no-op outright — same rule as `position`.
        if self.x is None and self.y is None:
            return True
        return (self.x is None or i.meta.align.x == self.x) and (self.y is None or i.meta.align.y == self.y)

    def modify(self, i: Input):
        # An axis left `None` is one this effect does NOT CLAIM, and it must
        # reach the stack as a hole. `position` was given this rule; `align` was
        # not, and the write-back below (`self.x, self.y = i.meta.align`) was
        # what filled the hole in: `alignTo(x=3)` then `alignTo(y=5)` erased the
        # x ramp, x jumping to its final value on frame 1 — while the identical
        # pair on `moveTo` composes.
        if self.x is not None:
            i.meta.align.x = self.x
        if self.y is not None:
            i.meta.align.y = self.y
