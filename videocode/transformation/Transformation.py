#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC
from videocode.Constant import *
from videocode.Global import Metadata


class Transformation(ABC):
    """
    Represents a `Transformation`.

    .. code-block:: python
        def move() -> Transformation: ...
        def zoom() -> Transformation: ...
        def fade() -> Transformation: ...
        def grayscale() -> Transformation: ...

    """

    duration: sec | default

    def modificator(self, i: Metadata):
        """
        Modify the `Input` if any of it's metadata should be updated.
        """
        ...

    def __str__(self) -> str:
        return str(vars(self))
