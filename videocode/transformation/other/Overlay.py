#!/usr/bin/env python3

from videocode.input.Input import Input
from videocode.transformation.Transformation import Transformation


class overlay(Transformation):
    def __init__(self, fg: Input) -> None:
        """
        Overlays `x` on top of `self`.
        """
        self.fg = fg.index
