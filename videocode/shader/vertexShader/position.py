#!/usr/bin/env python3


from videocode.shader.ishader import *


class position(VertexShader):
    """
    set the position `x` and `y` of an `Input`.

    - `None` doesn't change the position

    This takes action on all frames instantly, there is no delay.

    For a movement over time, see `moveTo`.
    """

    def __init__(self, x: maybe[wnumber] = None, y: maybe[wnumber] = None) -> None:
        self.x = x
        self.y = y
        # could be self.p = v2(x, y)
        # so we could use a setattr(attr) with the VertexShader and so remove the modificators

    def modificator(self, i: Input):
        if self.x is None:
            self.x = i.meta.position.x
        if self.y is None:
            self.y = i.meta.position.y

        i.meta.position = v2(self.x, self.y)
