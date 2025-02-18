#!/usr/bin/env python3

from frontend.input.Input import Input
from frontend.transformation.Transformation import Transformation


class merge(Transformation):
    def __init__(self, x: Input) -> None:
        """
        Concatenates `x` after `self`.
        """
        self.x = x.index
