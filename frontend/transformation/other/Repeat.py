#!/usr/bin/env python3

from frontend.input.Input import Input
from frontend.transformation.Transformation import Transformation
from frontend.Constant import uint


class repeat(Transformation):
    def __init__(self, n: uint) -> None:
        """
        Repeats `self` `n` times.
        """
        self.n = n
