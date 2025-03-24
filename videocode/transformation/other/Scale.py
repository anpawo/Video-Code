#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation

class scale(Transformation):
    """
    `Scale` an `Input` keeping the pixels outside the dimension of the `Input` unlike `Zoom`.
    """

    def __init__(self, *, factor: float | int | tuple[float, float] = 2, centered : bool = False) -> None:
        """
        :param factor: The scale factor. If a tuple, the first value is the x scale and the second value is the y scale.
        :param centered: If True, the scale is centered. If False, the scale is applied from the top left corner.
        """
        if isinstance(factor, tuple):
            self.factor = factor
        else:
            self.factor = (factor, factor)
        self.centered = centered
