#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self

import copy

from videocode.transformation.Transformation import Transformation
from videocode.Global import *
from videocode.Constant import *
from videocode.transformation.setter.SetPosition import setPosition


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

    """
    Metadata of the `Input`.
    """
    meta: Metadata

    """
    Index of the `Input`.
    """
    index: int

    def __new__(cls, *args, **kwargs) -> Self:
        instance = super().__new__(cls)
        instance.index = Global.getIndex()
        instance.meta = Global.getDefaultMetadata()
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
                "input": [self.index],
            }
        )
        return self

    def apply(self, *ts: Transformation, start: sec = default(0), duration: sec = default(1)) -> Input:  # type: ignore
        """
        Applies the `Transformations` `ts` to the `Input` `self`.

        The duration is in seconds, so it will affect `duration * framerate` frames of the video.
        """
        for t in ts:
            __start = getValueByPriority(t, start)
            __duration = getValueByPriority(t, duration)

            t.modificator(self.meta)

            Global.stack.append(
                {
                    "action": "Apply",
                    "input": self.index,
                    "transformation": t.__class__.__name__,
                    "args": vars(t) | {"start": __start} | {"duration": __duration},
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

    def setPosition(self, x: int | float | None = None, y: int | float | None = None):
        return self.apply(setPosition(x, y).enableSetter())

    # def __setattr__(self, name: str, value: Any) -> None:
    #     return super().__setattr__(name, value)
