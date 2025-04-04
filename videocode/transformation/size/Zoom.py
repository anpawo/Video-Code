#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation

from videocode.Constant import *


class zoom(Transformation):
    """
    `Zoom` an `Input` while keeping it's original width and height unlike `Scale`.
    """

    def __init__(
        self,
        *,
        factor: float = 2.0,
        x: position = 0.5,
        y: position = 0.5,
    ):
        self.factor = (1.0, factor)
        self.x = x
        self.y = y
