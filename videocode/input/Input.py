#!/usr/bin/env python3


from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self

from videocode.template.effect.fadeIn import fadeIn
from videocode.template.effect.fadeOut import fadeOut
from videocode.template.effect.moveTo import moveTo
from videocode.template.effect.moveBy import moveBy
from videocode.template.effect.scaleBy import scaleBy
from videocode.template.effect.scaleTo import scaleTo
from videocode.shader.ishader import IShader, VertexShader, FragmentShader
from videocode.globals import *
from videocode.constants import *
from videocode.utils.funcutils import *
from videocode.shader.vertexShader.align import align
from videocode.shader.vertexShader.args import args
from videocode.shader.vertexShader.hide import hide
from videocode.shader.vertexShader.rotate import rotate
from videocode.shader.vertexShader.scale import scale
from videocode.shader.vertexShader.position import position
from videocode.shader.vertexShader.show import show
from videocode.utils.bezier import cubicBezier, Easing


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

    def __new__(cls, *args, **kwargs) -> Self:
        instance = super().__new__(cls)
        instance.meta = Metadata(instance.__dict__)
        return instance

    @abstractmethod
    def __init__(self) -> None: ...

    def flush(self) -> Self:
        """
        Advance the transformation index offset to the latest frame ever modified.
        """
        self.meta.transformationOffset = self.meta.lastAffectedFrame
        return self

    def apply(self, *es: IShader, start: defaultable[sec] = default(0), duration: defaultable[sec] = default(1)) -> Self:
        """
        Applies some `Transformations` to the `Input`.

        The `duration` is in `seconds`, so it will affect `duration * framerate` frames of the video.
        """

        # If a `wait()` happens, any input should be flushed before applying any new effect.
        if Global.waitOffset >= self.meta.transformationOffset:
            self.meta.lastAffectedFrame = Global.waitOffset
            self.flush()

        for e in es:
            __start: int = int(getValueByPriority(e, start, "start") * FRAMERATE) + self.meta.transformationOffset
            __duration: int = int(getValueByPriority(e, duration, "duration") * FRAMERATE)

            # Update lastEverAffectedFrame
            if Global.lastEverAffectedFrame < __start + __duration:
                Global.lastEverAffectedFrame = __start + __duration

            # Update our lastAffectedFrame
            if __start + __duration > self.meta.lastAffectedFrame:
                self.meta.lastAffectedFrame = __start + __duration

            # Transformations affect the Input's Metadata
            if isinstance(e, VertexShader):
                e.modificator(self)

            # Add step to the stack
            Global.stack.append(
                {
                    "action": "Apply",
                    "input": self.meta.index,
                    "name": upperFirst(e.__class__.__name__),
                    "type": e._type,
                    "args": fromWorlToScreen(e.__init__.__annotations__, vars(e)) | {"start": __start} | {"duration": __duration},
                }
            )

        return self

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            self.apply(args(name, fromWorlToScreen(self.__class__.__annotations__, {name: value})[name]))
        else:
            object.__setattr__(self, name, value)

    def __str__(self) -> str:
        s = f"\n{self.__class__.__name__}:\n"
        for k, v in self.__dict__.items():
            s += f"\t{k}={v}\n"
        return s

    def __repr__(self) -> str:
        return self.__str__()

    ### Transformations ###

    def position(self, x: maybe[number] = None, y: maybe[number] = None) -> Self:
        return self.apply(position(x, y))

    def scale(self, factor: maybe[number] = None, *, x: maybe[number] = None, y: maybe[number] = None) -> Self:
        if factor is not None:
            x = factor
            y = factor
        return self.apply(scale(x=x, y=y))

    def rotate(self, degree: number) -> Self:
        return self.apply(rotate(degree))

    def align(self, x: maybe[number] = None, y: maybe[number] = None) -> Self:
        return self.apply(align(x, y))

    def hide(self, start: sec = 0):
        return self.apply(hide(), start=start)

    def show(self, start: sec = 0):
        return self.apply(show(), start=start)

    ### Template ###

    def moveTo(self, x: maybe[number] = None, y: maybe[number] = None, easing: cubicBezier = Easing.Out, start: sec = 0, duration: sec = 0.4) -> Self:
        moveTo(self, x=x, y=y, easing=easing, start=start, duration=duration)
        return self

    def moveBy(self, x: maybe[number] = None, y: maybe[number] = None, easing: cubicBezier = Easing.Out, start: sec = 0, duration: sec = 0.4) -> Self:
        moveBy(self, x=x, y=y, easing=easing, start=start, duration=duration)
        return self

    def fadeIn(self, *, easing: cubicBezier = Easing.Out, start: sec = 0, duration: sec = 0.4) -> Self:
        fadeIn(self, easing=easing, start=start, duration=duration)
        return self

    def fadeOut(self, *, easing: cubicBezier = Easing.Out, start: sec = 0, duration: sec = 0.4) -> Self:
        fadeOut(self, easing=easing, start=start, duration=duration)
        return self

    def scaleTo(self, factor: maybe[number] = None, *, x: maybe[number] = None, y: maybe[number] = None, easing: cubicBezier = Easing.Out, start: sec = 0, duration: sec = 0.4) -> Self:
        if factor is not None:
            x = factor
            y = factor
        scaleTo(self, x=x, y=y, easing=easing, start=start, duration=duration)
        return self

    def scaleBy(self, factor: maybe[number] = None, *, x: maybe[number] = None, y: maybe[number] = None, easing: cubicBezier = Easing.Out, start: sec = 0, duration: sec = 0.4) -> Self:
        if factor is not None:
            x = factor
            y = factor
        scaleBy(self, x=x, y=y, easing=easing, start=start, duration=duration)
        return self
