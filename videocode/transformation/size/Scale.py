#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation


class scale(Transformation):
    """
    `Scale` will scale up or down an `Input` according to `factor` while changing it's original width and height.

    # TODO: add a position where the scaling should take place from, it will move the input
    """

    def __init__(
        self,
        factor: float = 2.0,
    ):
        self.factor = factor
