#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Self

from videocode.template.movement.moveTo import moveTo
from videocode.transformation.Transformation import Effect, Transformation
from videocode.Global import *
from videocode.Constant import *
from videocode.Utils import *
from videocode.transformation.transformation.Align import align
from videocode.transformation.transformation.Args import args
from videocode.transformation.transformation.Hide import hide
from videocode.transformation.transformation.Rotate import rotate
from videocode.transformation.transformation.Scale import scale
from videocode.transformation.transformation.Position import position
from videocode.transformation.transformation.Show import show
from videocode.utils.bezier import cubicBezier
from videocode.utils.easings import Easing


class Input(ABC):
    """
    An `Input` is a source that you want to add to the timeline of the video.

    It can be an `Image`, a `Video`, a `Shape`, some `Text` etc...

    Example:
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
    inputIndex: int | None

    def __new__(cls, *args, **kwargs) -> Self:
        instance = super().__new__(cls)
        instance.inputIndex = Global.getIndex()
        instance.meta = Metadata(instance.__dict__)
        return instance

    @abstractmethod
    def __init__(self) -> None: ...

    def flush(self) -> Self:
        """
        Advance the transformation index offset to the latest.
        """
        # TODO: needs a fix, something's off
        if self.meta.transformationIndexOffset < self.meta.lastAffectedFrameIndex:
            self.meta.transformationIndexOffset = self.meta.lastAffectedFrameIndex
        return self

    def apply(self, *ts: Effect, start: t = default(0), duration: t = default(1)) -> Self:
        """
        Applies some `Transformations` to the `Input`.

        The `duration` is in `seconds`, so it will affect `duration * framerate` frames of the video.
        """
        for t in ts:
            __start = getValueByPriority(t, start, "start") * FRAMERATE + self.meta.transformationIndexOffset
            __duration = getValueByPriority(t, duration, "duration") * FRAMERATE
            # Without any check it flushs the last added tsf, not the latest
            self.meta.lastAffectedFrameIndex = __start + __duration

            if isinstance(t, Transformation):
                t.modificator(self.meta)

            Global.stack.append(
                {
                    "action": "Apply",
                    "input": self.inputIndex,
                    "transformation": upperFirst(t.__class__.__name__),
                    "type": t._type,
                    "args": vars(t) | {"start": __start} | {"duration": __duration},
                }
            )

        return self

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            self.apply(args(name, value))
        object.__setattr__(self, name, value)

    def __str__(self) -> str:
        s = f"\n{self.__class__.__name__}:\n"
        for k, v in self.__dict__.items():
            s += f"\t{k}=;{v};\n"
        return s

    def __repr__(self) -> str:
        return self.__str__()

    ### Transformations ###

    def position(self, x: number | None = None, y: number | None = None) -> Self:
        return self.apply(position(x, y))

    def scale(self, x: number) -> Self:
        return self.apply(scale(x))

    def rotate(self, x: number) -> Self:
        return self.apply(rotate(x))

    def align(self, x: number | None = None, y: number | None = None) -> Self:
        return self.apply(align(x, y))

    def hide(self, start: sec = 0):
        return self.apply(hide(), start=start)

    def show(self, start: sec = 0):
        return self.apply(show(), start=start)

    def moveTo(self, x: number | None = None, y: number | None = None, *, easing: cubicBezier = Easing.Out, start: sec = 0, duration: sec = 0.4) -> Self:
        moveTo(self, x, y, easing=easing, start=start, duration=duration)
        return self

    # TODO: Base loop with scaling function like bezier (from -> to, time, fn)
