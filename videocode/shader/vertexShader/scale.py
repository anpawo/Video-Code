#!/usr/bin/env python3

from videocode.ty import *
from videocode.constants import *
from videocode.shader.ishader import *


class scale(VertexShader):
    """
    `Scale` will scale up or down an `Input` according to `factor` while changing it's original width and height.

    # TODO: a position where the scaling should take place from, it will move the input
    """

    def __init__(
        self,
        x: maybe[number],
        y: maybe[number],
    ):
        self.x = x
        self.y = y

    def modificator(self, i: Input):
        # Update the scaling of the Input
        if self.x is not None:
            i.meta.scale.x = self.x
        else:
            self.x = i.meta.scale.x

        if self.y is not None:
            i.meta.scale.y = self.y
        else:
            self.y = i.meta.scale.y
