#!/usr/bin/env python3

from videocode.constants import *
from videocode.shader.ishader import *


class align(VertexShader):
    """
    set the alignment of `x` and `y` of an `Input`.

    can be `None` if you only want to change one of the two.
    """

    def __init__(self, x: number | None = None, y: number | None = None) -> None:
        self.x: number | None = x
        self.y: number | None = y

    def modificator(self, i: Input):
        # Update the alignment of the Input
        if self.x is not None:
            i.meta.align.x = self.x
        else:
            self.x = i.meta.align.x

        if self.y is not None:
            i.meta.align.y = self.y
        else:
            self.y = i.meta.align.y
