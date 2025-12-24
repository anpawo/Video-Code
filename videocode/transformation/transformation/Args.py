#!/usr/bin/env python3


from typing import Any
from videocode.Global import Metadata
from videocode.transformation.Transformation import Transformation


class args(Transformation):
    """
    Modifies the arguments needed to create the base matrix of an `Input`, e.g. the radius of a circle.
    """

    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self.value = value

    def modificator(self, meta: Metadata):
        meta.args[self.name] = self.value
