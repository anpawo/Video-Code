#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class blur(FragmentShader):
    """
    `Blur` an `Input`.

    Strength must be `odd` and `positive`.
    """

    def __init__(
        self,
        strength: unumber = 1.0,
    ):
        self.strength = strength
