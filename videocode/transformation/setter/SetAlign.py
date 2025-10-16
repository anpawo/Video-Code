#!/usr/bin/env python3

from videocode.Constant import *
from videocode.Global import Metadata
from videocode.transformation.setter.Setter import Setter


class setAlign(Setter):
    """
    set the alignment of `x` and `y` of an `Input`.

    can be `None` if you only want to change one of the two.
    """

    def __init__(self, x: align | None = None, y: align | None = None, **kwargs) -> None:
        self.x: align | None = x
        self.y: align | None = y

    def modificator(self, meta: Metadata):
        # Update the alignment of the Input
        if self.x is not None:
            meta.alignX = self.x
        if self.y is not None:
            meta.alignY = self.y
