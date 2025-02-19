#!/usr/bin/env python3

from frontend.input.Input import Input
from frontend.transformation.Transformation import Transformation


class overlay(Transformation):
    def __init__(self, fg: Input) -> None:
        """
        Overlays `x` on top of `self`.
        """
        self.fg = fg.index
