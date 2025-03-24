#!/usr/bin/env python3

from typing import Generator, Iterator
from videocode.transformation.Transformation import Transformation

from videocode.Constant import *


class zoom(Transformation):
    """
    `Zoom` an `Input` not keeping the pixels outside the dimension of the `Input` unlike `Scale`.
    """

    def __init__(
        self,
        factor: float | int | tuple[float, float] = 2,
        x: position = 0.5,
        y: position = 0.5,
    ) -> None:
        if isinstance(factor, tuple):
            self.factor = factor
        else:
            self.factor = (factor, factor)
        self.x = x
        self.y = y
