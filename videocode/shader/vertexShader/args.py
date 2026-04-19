#!/usr/bin/env python3


from typing import Any
from videocode.shader.ishader import *


class args(VertexShader):
    """
    Modifies the arguments needed to create the base matrix of an `Input`, e.g. the radius of a circle.

    Should not be instantiated on its own but only through __setattr__.
    """

    def __init__(self, name: str, value: Any, annotation: type | None) -> None:
        self.name = name
        self.value = value
        # Override annotation
        self.__init__.__annotations__["value"] = annotation

    def modificator(self, _: Input):
        """
        input.__setattr__ creates an `args VertexShader`.

        args does nothing in the python API.
        """
