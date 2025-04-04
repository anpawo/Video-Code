#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation


class scale(Transformation):
    """
    `Scale` an `Input` while changing it's original width and height unlike `Zoom`.
    """

    def __init__(
        self,
        *,
        factor: float = 2.0,
    ):
        self.factor = (1.0, factor)
