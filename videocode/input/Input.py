#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self

import copy

from videocode.transformation.Transformation import Transformation
from videocode.Global import *
from videocode.Constant import *


class Input(ABC):
    """
    Represents an `Input` which is a list of frames.

    A frame is a matrix of pixel. `1 second` == `24 frames`.

    You cannot create an `Input` from the base class.

    Basic `Inputs`:
    .. code-block:: python
        def image(filepath: str) -> Input: ...
        def video(filepath: str) -> Input: ...
        def text(string: str) -> Input: ...
        def circle(radius: int) -> Input: ...
    """

    index: int
    """
    Index of the `Input`.
    """

    def __new__(cls, *args, **kwargs) -> Self:
        instance = super().__new__(cls)
        instance.index = Global.getIndex()
        return instance

    @abstractmethod
    def __init__(self) -> None: ...

    def add(self) -> Self:
        """
        Appends the `frames` of `self` to the `timeline`.
        """
        Global.stack.append(
            {
                "action": "Add",
                "input": self.index,
            }
        )
        return self

    def apply(self, *ts: Transformation, startTime: Defaultable[sec] = default(None), endTime: Defaultable[sec | None] = default(None)) -> Input:
        """
        Applies the `Transformations` `ts` to all the `frames` of `self` between [`startTime`, `endTime`].
        """
        for t in ts:
            if hasattr(t, "startTime"):
                startTime = t.startTime
                del t.startTime
            elif isinstance(startTime, default):
                startTime = startTime.defaultValue

            if hasattr(t, "endTime"):
                endTime = t.endTime
                del t.endTime
            elif isinstance(endTime, default):
                endTime = endTime.defaultValue

            Global.stack.append(
                {
                    "action": "Apply",
                    "input": self.index,
                    "transformation": t.__class__.__name__,
                    "args": vars(t),
                    "startTime": startTime,
                    "endTime": endTime,
                }
            )
        return self

    def copy(self) -> Input:
        """
        Creates a `copy` of `self`.
        """
        cp = copy.deepcopy(self)
        cp.index = Global.getIndex()
        Global.stack.append(
            {
                "action": "Create",
                "type": "Copy",
                "input": self.index,
            }
        )
        return cp

    def keep(self) -> None:
        Global.stack.append(
            {
                "action": "Keep",
                "input": self.index,
            }
        )

    def drop(self) -> None:
        Global.stack.append(
            {
                "action": "Drop",
                "input": self.index,
            }
        )

    def __getitem__(self, i: int | slice[int | None, int | None, None]) -> Slice:
        """
        Creates a `reference` of the `frames` `i`.

        Usefull if you want to apply a `Transformation` to a part of a video.

        ---
        ### Example
        >>> v = video("test.mp4")
        >>> v[0:20].apply(fadeIn()) # fade in during the first 20 frames.
        >>> v.add() # adds it to the timeline

        """
        if isinstance(i, int):
            s = slice(i, i + 1)  # stop is excluded
        else:
            s = slice(i.start or 0, i.stop or -1)

        # `Slice` of `Slice`
        if isinstance(self, Slice):
            start = -1 if s.start == -1 or self.s.start == -1 else self.s.start + s.start
            stop = -1 if s.stop == -1 else self.s.start + s.stop
            s = slice(start, stop)

        temp = Slice(self, s)
        Global.stack.append(
            {
                "action": "Create",
                "type": "Slice",
                "input": self.index,
                "start": s.start,
                "stop": s.stop,
            }
        )
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
