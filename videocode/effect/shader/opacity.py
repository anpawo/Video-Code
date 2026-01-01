#!/usr/bin/env python3

from videocode.effect.effect import *
from videocode.ty import *


class opacity(Shader):
    """
    `Fade` affects the opacity of an element.
    """

    duration = SINGLE_FRAME

    def __init__(
        self,
        opacity: uint,
    ):
        self.opacity = opacity
