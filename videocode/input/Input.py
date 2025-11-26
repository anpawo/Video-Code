#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Self

import copy

from videocode.template.movement.moveTo import moveTo
from videocode.transformation.Transformation import Transformation
from videocode.Global import *
from videocode.Constant import *
from videocode.transformation.setter.SetAlign import setAlign
from videocode.transformation.setter.SetPosition import setPosition
from videocode.transformation.setter.Setter import setArgument
from videocode.utils.bezier import cubicBezier
from videocode.utils.easings import Easing


class Input(ABC):
    """
    Represents an `Input` which is a list of frames.

    A frame is a matrix of pixel. `1 second` == `30 frames`.

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

    Groups do not have an index (they are just python wrapper)
    """
    index: int | None

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

        The first add also displays the `Input`.
        """

        # Prevent double add error
        if Global.automaticAdder:
            return self

        Global.stack.append(
            {
                "action": "Add",
                "input": self.index,
            }
        )
        return self

    @staticmethod
    def autoAdd(f: Callable[..., Input]):
        """
        Appends the `frames` of `self` to the `timeline` automatically after applying a `Transformation`.
        """

        def autoAddWrapper(*args, **kwargs):
            input = f(*args, **kwargs)

            if Global.automaticAdder:
                Global.stack.append(
                    {
                        "action": "Add",
                        "input": input.index,
                    }
                )

            return input

        return autoAddWrapper

    @autoAdd
    def apply(self, *ts: Transformation, start: t = default(0), duration: t = default(1)) -> Self:
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

    def setPosition(self, x: number | None = None, y: number | None = None) -> Self:
        return self.apply(setPosition(x, y))

    def moveTo(self, x: number | None = None, y: number | None = None, *, easing: cubicBezier = Easing.Out, start: sec = 0, duration: sec = 0.4) -> Self:
        moveTo(self, x, y, easing=easing, start=start, duration=duration)
        return self

    def setAlign(self, x: align | None = None, y: align | None = None) -> Self:
        return self.apply(setAlign(x, y))

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            # print(f"name=[{name}], value=[{value}], index=[{self.index}], self=[{str(self)}]")
            self.apply(setArgument(name, value))
        object.__setattr__(self, name, value)

    def __str__(self) -> str:
        s = f"\n{self.__class__.__name__}:\n"
        for i in self.__dict__:
            s += f"\t{i}='{self.__getattribute__(i)}'\n"
        return s

    def __repr__(self) -> str:
        return self.__str__()
