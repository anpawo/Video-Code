#!/usr/bin/env python3


from videocode.constants import *
from videocode.shader.ishader import *


class position(VertexShader):
    """
    set the position `x` and `y` of an `Input`.

    - `None` doesn't change the position

    This takes action on all frames instantly, there is no delay.

    For a movement over time, see `moveTo`.
    """

    def __init__(self, x: maybe[wint | wfloat] = None, y: maybe[wint | wfloat] = None) -> None:
        self.x = x
        self.y = y

    def modificator(self, i: Input):
        # Update the position of the Input
        if self.x is not None:
            i.meta.position.x = self.x
        else:
            self.x = i.meta.position.x

        if self.y is not None:
            i.meta.position.y = self.y
        else:
            self.y = i.meta.position.y
