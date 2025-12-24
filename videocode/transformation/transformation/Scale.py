#!/usr/bin/env python3

from videocode.Global import Metadata
from videocode.transformation.Transformation import Transformation
from videocode.Constant import number


class scale(Transformation):
    """
    `Scale` will scale up or down an `Input` according to `factor` while changing it's original width and height.

    # TODO: a position where the scaling should take place from, it will move the input
    """

    def __init__(
        self,
        factor: number | tuple[number, number],
    ):
        if isinstance(factor, int | float):
            self.x = factor
            self.y = factor
        else:
            self.x = factor[0]
            self.y = factor[1]

    def modificator(self, meta: Metadata):
        meta.rotation
