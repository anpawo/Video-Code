#!/usr/bin/env python3

from videocode.effect.effect import Shader
from videocode.ty import *


class opacity(Shader):
    """
    Change the `Opacity` of an `Input`.
    """

    def __init__(
        self,
        opacity: unumber,
    ):
        self.opacity = opacity
