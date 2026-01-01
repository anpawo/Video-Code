#!/usr/bin/env python3

from videocode.effect.effect import SingleFrameShader
from videocode.ty import *


class opacity(SingleFrameShader):
    """
    Change the `Opacity` of an `Input`.
    """

    def __init__(
        self,
        opacity: unumber,
    ):
        self.opacity = opacity
