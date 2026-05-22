#!/usr/bin/env python3


from typing import Any
from videocode.shader.ishader import *
from videocode.utils.logger import *


class args(VertexShader):
    """
    Modifies the arguments needed to create the base matrix of an `Input`, e.g. the radius of a circle.

    Should not be instantiated on its own but only through Input.__setattr__.
    """

    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self.value = value

    # Already checked in Input.__setattr__
    # def autodestroy(self, i: Input) -> bool: ...

    def modify(self, _: Input):
        """
        Input.__setattr__ has already been called.
        """
        object.__setattr__(self, self.name, self.value)
