#!/usr/bin/env python3

from videocode.input.Input import Input
from videocode.transformation.Transformation import Transformation
from videocode.Constant import uint


class repeat(Transformation):
    def __init__(self, n: uint) -> None:
        """
        Repeats `self` `n` times.
        """
        self.n = n
