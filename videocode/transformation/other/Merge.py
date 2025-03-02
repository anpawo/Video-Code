#!/usr/bin/env python3

from videocode.input.Input import Input
from videocode.transformation.Transformation import Transformation


class merge(Transformation):
    def __init__(self, x: Input) -> None:
        """
        Merges with `x`.

        Each `Input` will have the same ratio on the result.
        """
        self.x = x.index
