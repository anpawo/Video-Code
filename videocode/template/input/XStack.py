#!/usr/bin/env python3

from __future__ import annotations

from videocode.input.interface.Group import Group
from videocode.input.input import Input
from videocode.ty import *
from videocode.constants import *

__all__ = ["XStack"]


class XStack(Group):
    def __init__(self, gap: wnumber = 0.1):
        self.gap = gap
        self.curX: wnumber = 0.0
        super().__init__()

    def add(self, inp: Input) -> Self:
        w = inp.width
        localX = self.curX + w / 2
        inp.position((self.meta.position.x or 0) + localX, self.meta.position.y)
        self.curX += w + self.gap
        self.inputs.append(inp)
        return self
