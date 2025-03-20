#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation

class scale(Transformation):
    """
    `Scale` an `Input` keeping the pixels outside the dimension of the `Input` unlike `Zoom`.
    """

    def __init__(self, *, factor: float | int | tuple[float, float] = 2) -> None:
        if isinstance(factor, tuple):
            self.factor = factor
        else:
            self.factor = (factor, factor)
