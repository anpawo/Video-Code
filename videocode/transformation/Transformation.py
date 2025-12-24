#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from videocode.Constant import *
from videocode.Utils import *
from videocode.Global import Metadata


class Effect(ABC):
    """
    An `Effect` modifies the pixels of an image.

    .. code-block:: python
        def fade() -> Effect: ...
        def grayscale() -> Effect: ...

    """

    _type = "effect"

    duration: t

    def __str__(self) -> str:
        s = f"\n{self.__class__.__name__}:\n"
        for i in self.__dict__:
            s += f"\t{i}='{self.__getattribute__(i)}'\n"
        return s

    def __repr__(self) -> str:
        return self.__str__()


class Transformation(Effect):
    """
    A `Transformation` modifies the metadata of an image, anything not related to pixel, e.g. position.

    .. code-block:: python
        def position() -> Transformation: ...
        def scale() -> Transformation: ...

    """

    _type = "transformation"

    """
    affects only one frame
    """
    duration = SF

    @abstractmethod
    def modificator(self, _: Metadata):
        """
        Modify the `Input`'s `Metadata`.

        We want the python interface to keep trace of the changes made on the inputs but they need
        to be applied the moment the transformations are applied, not the moment they are created.
        """
