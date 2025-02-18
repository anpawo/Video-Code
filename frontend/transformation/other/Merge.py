#!/usr/bin/env python3

from frontend.input.Input import Input
from frontend.transformation.Transformation import Transformation


class merge(Transformation):
    def __init__(self, x: Input) -> None:
        """
        Merges with `x`.

        Each `Input` will have the same ratio on the result.
        """
        self.x = x.index
