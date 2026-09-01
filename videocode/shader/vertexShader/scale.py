#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *
from videocode.utils.classutils import Maybe


class scale(VertexShader):
    _rigidKind = 3
    """
    `Scale` up or down an `Input`'s size.
    """

    def __init__(self, x: maybe[number], y: maybe[number], *, about: maybe[v2] = None):
        self.x = x
        self.y = y
        #: Where the scaling happens from — see `rotation.about`.
        self.about = about

    def autodestroy(self, i: Input) -> bool:
        # Claiming nothing at all is a no-op outright — same rule as `position`.
        if self.x is None and self.y is None:
            return True
        return (self.x is None or i.meta.scale.x == self.x) and (self.y is None or i.meta.scale.y == self.y)

    def modify(self, i: Input):
        # An axis left `None` is one this effect does NOT CLAIM, and it must
        # reach the stack as a hole. `position` was given this rule; `scale` was
        # not, and the write-back below (`self.x, self.y = i.meta.scale`) was
        # what filled the hole in: `scaleTo(x=3)` then `scaleTo(y=5)` erased the
        # x ramp, x jumping to its final value on frame 1 — while the identical
        # pair on `moveTo` composes.
        if self.x is not None:
            i.meta.scale.x = self.x
        if self.y is not None:
            i.meta.scale.y = self.y
