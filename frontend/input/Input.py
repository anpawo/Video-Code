#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
import copy
from typing import Any, Self, overload

from frontend.transformation.Transformation import Transformation
from frontend.Global import *


class Input(ABC):
    """
    Represents an `Input` which is a list of frames.

    A frame is a matrix of pixel. `1 second` == `24 frames`.

    You cannot create an `Input` from the base class.

    .. code-block:: python
        def image(filepath: str) -> Input: ...
        def video(filepath: str) -> Input: ...
        def text(string: str) -> Input: ...
        def shape() -> Input: ...
    """

    index: int

    def __new__(cls, *args, **kwargs) -> Self:
        instance = super().__new__(cls)
        instance.index = len(Global.requiredInputs)
        return instance

    @abstractmethod
    def __init__(self) -> None: ...

    def add(self) -> None:
        """
        Appends the `frames` of `self` to the `timeline`.
        """
        Global.transformationStack.append(("Add", self.index, []))

    def apply(self, *ts: Transformation) -> Input:
        """
        Applies the `Transformations` `ts` to all the `frames` of `self`.
        """
        for t in ts:
            Global.transformationStack.append(("Apply", self.index, [t.__class__.__name__, t.attributes()]))
        return self

    def copy(self) -> Input:
        """
        Creates a `copy` of `self`.
        """
        cp = copy.deepcopy(self)
        cp.index = len(Global.requiredInputs)
        Global.requiredInputs.append(("Copy", [self.index]))
        return cp

    def __getitem__(self, i: int | slice[int, int, None]) -> Slice:
        """
        Creates a `reference` of the `frames` `s`.

        Usefull if you want to apply a `Transformation` to a part of a video.

        Examples
        --------
        >>> v = video("test.mp4")
        >>> v[0:20].fade() # Fade-in during the first 20 frames.
        >>> v.add()
        """
        if isinstance(i, int):
            s = slice(i, i)
        else:
            s = i

        if isinstance(self, Slice):
            start = -1 if s.start == -1 or self.s.start == -1 else self.s.start + s.start
            stop = -1 if s.stop == -1 else self.s.start + s.stop
            s = slice(start, stop)

        temp = Slice(self, s)
        Global.requiredInputs.append(("Slice", [self.index, s.start, s.stop]))
        return temp


class Slice(Input):
    """
    Sliced `Input`.

    This class only exists for subsequent slices.
    """

    def __init__(self, i: Input, s: slice) -> None:
        """
        The base `Input` is `i`.

        The sliced portion is `s`.
        """
        self.i = i
        self.s = s
