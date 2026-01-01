#!/usr/bin/env python3

from videocode.effect.effect import SingleFrameShader
from videocode.ty import unumber


class blur(SingleFrameShader):
    """
    `Blur` an `Input`.

    Strength must be `odd` and `positive`.
    """

    def __init__(
        self,
        strength: unumber = 1.0,
    ):
        self.strength = strength
