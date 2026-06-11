#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self
from videocode.constants import *
from videocode.utils.funcutils import *
from videocode.utils.classutils import Maybe

if TYPE_CHECKING:
    from videocode.input.input import Input


class IShader(ABC):
    """
    A `Effect` modifies an input.
    """

    _type: str

    start: maybe[sec] = None
    duration: maybe[sec] = None
    offset: maybe[frame] = None

    def at(self, *, start: sec, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        self.start = start
        self.duration = duration
        self.offset = offset
        return self

    def resolve(self, start: sec, duration: sec, offset: maybe[frame]) -> tuple[sec, sec, maybe[frame]]:
        """
        Use self default values if any else given ones.
        """
        return (
            Maybe(self.start) | start,
            Maybe(self.duration) | duration,
            Maybe(self.offset) | offset,
        )

    @abstractmethod
    def __init__(self) -> None: ...

    def __str__(self) -> str:
        s = f"{self.__class__.__name__}"
        return s

    def __repr__(self) -> str:
        return self.__str__()


class FragmentShader(IShader):
    """
    An `FragmentShader` modifies the pixels of an `Input`.
    """

    _type = "FragmentShader"


class VertexShader(IShader):
    """
    A `VertexShader` modifies the metadata of an `Input`.

    ### Geometry
    - position
    - align
    - rotate
    - scale

    ### Visibility
    - opacity
    - hide
    - show

    ### Default arguments of an Input
    - args
    """

    _type = "VertexShader"

    def autodestroy(self, i: Input) -> bool:
        return False

    @abstractmethod
    def modify(self, i: Input) -> None:
        """
        Modify the `Input`'s `Metadata`. (may do more)

        We want the python interface to keep trace of the changes made on the inputs but they need
        to be applied the moment the transformations are applied, not the moment they are created.
        """
