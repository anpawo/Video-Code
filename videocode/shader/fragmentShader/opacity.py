#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import *


class opacity(FragmentShader):
    """
    Change the `Opacity` of an `Input`.
    """

    def __init__(
        self,
        opacity: unumber,
    ):
        self.opacity = opacity
