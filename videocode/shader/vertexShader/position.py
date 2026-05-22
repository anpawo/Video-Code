#!/usr/bin/env python3


from videocode.shader.ishader import *
from videocode.utils.classutils import Maybe


class position[T1: mnbr = number, T2: mnbr = number](VertexShader):
    """
    set the position `x` and `y` of an `Input`.

    - `None` doesn't change the position

    This takes action on all frames instantly, there is no delay.

    For a movement over time, see `moveTo`.
    """

    def __init__(self, x: T1, y: T2) -> None:
        self.x = x
        self.y = y
        # since it can be None, some compaapny
        # could be self.p = v2(x, y)
        # TODO: so we could use a setattr(attr) with the VertexShader and so remove the modificators

    def autodestroy(self, i: Input) -> bool:
        return (i.meta.position.x is None or i.meta.position.x == self.x) and (i.meta.position.y is None or i.meta.position.y == self.y)

    def modify(self, i: Input):
        self.x = i.meta.position.x = self.x if self.x is not None else i.meta.position.x
        self.y = i.meta.position.y = self.y if self.y is not None else i.meta.position.y
