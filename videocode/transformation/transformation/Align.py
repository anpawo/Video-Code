#!/usr/bin/env python3

from videocode.Constant import *
from videocode.Global import Metadata
from videocode.transformation.Transformation import Transformation


class align(Transformation):
    """
    set the alignment of `x` and `y` of an `Input`.

    can be `None` if you only want to change one of the two.
    """

    def __init__(self, x: number | None = None, y: number | None = None) -> None:
        self.x: number | None = x
        self.y: number | None = y

    def modificator(self, meta: Metadata):
        # Update the alignment of the Input
        if self.x is not None:
            meta.align.x = self.x
        else:
            self.x = meta.align.x

        if self.y is not None:
            meta.align.y = self.y
        else:
            self.y = meta.align.y
