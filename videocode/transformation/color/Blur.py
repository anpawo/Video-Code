#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation


class blur(Transformation):
    """
    `blur` `Transformation`. Persistent defines if you want it to be shown on the following frames.
    """

    def __init__(
        self,
        strength: float = 2.0,
    ):
        self.strength = strength
