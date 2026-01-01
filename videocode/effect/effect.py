#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.utils.funcutils import *

if TYPE_CHECKING:
    from videocode.input.input import Input


class Effect(ABC):
    """
    A `Effect` modifies an input.
    """

    _type: str

    duration: sec

    @abstractmethod
    def __init__(self) -> None: ...

    def __str__(self) -> str:
        s = f"\n{self.__class__.__name__}:\n"
        for i in self.__dict__:
            s += f"\t{i}='{self.__getattribute__(i)}'\n"
        return s

    def __repr__(self) -> str:
        return self.__str__()


class Shader(Effect):
    """
    An `Shader` modifies the pixels of an image.

    .. code-block:: python
        def fade() -> Effect: ...
        def grayscale() -> Effect: ...

    """

    _type = "shader"


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
    duration = SINGLE_FRAME

    @abstractmethod
    def modificator(self, i: Input):
        """
        Modify the `Input`'s `Metadata`. (may do more)

        We want the python interface to keep trace of the changes made on the inputs but they need
        to be applied the moment the transformations are applied, not the moment they are created.
        """
