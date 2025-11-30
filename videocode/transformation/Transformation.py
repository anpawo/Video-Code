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
        def scale() -> Transformation: ...
        def fade() -> Transformation: ...
        def grayscale() -> Transformation: ...

    """

    duration: t

    def modificator(self, _: Metadata):
        """
        Modify the `Input`'s `Metadata` if it should be updated.
        """
        ...

    def __str__(self) -> str:
        s = f"\n{self.__class__.__name__}:\n"
        for i in self.__dict__:
            s += f"\t{i}='{self.__getattribute__(i)}'\n"
        return s

    def __repr__(self) -> str:
        return self.__str__()
