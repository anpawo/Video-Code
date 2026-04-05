#!/usr/bin/env python3


from videocode.shader.ishader import *


class opacity(VertexShader):
    """
    Change the `Opacity` of an `Input`.
    """

    def __init__(
        self,
        opacity: number,
    ):
        self.opacity = opacity

    def modificator(self, i: Input):
        i.meta.opacity = self.opacity
