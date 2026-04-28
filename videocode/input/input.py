#!/usr/bin/env python3


from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Self
from videocode.template.effect.fadeIn import fadeIn
from videocode.template.effect.fadeOut import fadeOut
from videocode.template.effect.moveTo import moveTo
from videocode.template.effect.moveBy import moveBy
from videocode.template.effect.scaleBy import scaleBy
from videocode.template.effect.scaleTo import scaleTo
from videocode.shader.ishader import IShader, VertexShader, FragmentShader
from videocode.context import *
from videocode.constants import *
from videocode.utils.decorators import timed
from videocode.utils.funcutils import *
from videocode.shader.vertexShader.align import align
from videocode.shader.vertexShader.args import args
from videocode.shader.vertexShader.hide import hide
from videocode.shader.vertexShader.rotate import rotate
from videocode.shader.vertexShader.scale import scale
from videocode.shader.vertexShader.position import position
from videocode.shader.vertexShader.show import show
from videocode.shader.vertexShader.opacity import opacity
from videocode.utils.bezier import animate, CubicBezier, Easing
from videocode.utils.logger import *


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
        instance.meta = Metadata()
        return instance

    @abstractmethod
    def __init__(self) -> None: ...

    def flush(self) -> Self:
        """
        Advance the transformation index offset to the latest frame ever modified.
        """
        self.meta.transformationOffset = self.meta.lastAffectedFrame
        return self

    def waitTo(self, n: frame) -> Self:
        self.meta.transformationOffset = self.meta.lastAffectedFrame = n
        return self

    def wait(self, n: sec) -> Self:
        self.meta.transformationOffset = self.meta.lastAffectedFrame = int(n * FRAMERATE)
        return self

    def waitFor(self, i: Input) -> Self:
        return self.waitTo(i.meta.lastAffectedFrame)

    def apply(self, *shaders: IShader, start: defaultable[sec] = default(0), duration: defaultable[sec] = default(1)) -> Self:
        """
        Applies some `Transformations` to the `Input`.

        The `duration` is in `seconds`, so it will affect `duration * framerate` frames of the video.
        """

        # If a `wait()` happens, any input should be flushed before applying any new effect.
        if Context.waitOffset >= self.meta.transformationOffset:
            self.meta.transformationOffset = self.meta.lastAffectedFrame = Context.waitOffset

        for s in shaders:
            __start: int = int(getValueByPriority(s, start, "start") * FRAMERATE) + self.meta.transformationOffset
            __duration: int = int(getValueByPriority(s, duration, "duration") * FRAMERATE)

            # Update lastEverAffectedFrame
            if Context.lastEverAffectedFrame < __start + __duration:
                Context.lastEverAffectedFrame = __start + __duration

            # Update our lastAffectedFrame
            if __start + __duration > self.meta.lastAffectedFrame:
                self.meta.lastAffectedFrame = __start + __duration

            # Transformations affect the Input's Metadata
            if isinstance(s, VertexShader):
                s.modificator(self)

            # Add step to the stack
            Context.stack.append(
                {
                    "action": "Apply",
                    "input": self.meta.index,
                    "name": upperFirst(s.__class__.__name__),
                    "type": s._type,
                    "args": vars(s) | {"start": __start} | {"duration": __duration},
                }
            )

        return self

    ### Builtins ###

    def __enter__(self):
        self.meta.setattrCallbackOn = True
        return self

    def __exit__(self, excType, excValue, traceback):
        self.meta.setattrCallbackOn = False
        return False

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, "meta") and self.meta.setattrCallbackOn and not name in self.meta.props:
            annotation = self.__class__.__annotations__.get(name)
            start = self.meta.pendingSetattrStart
            duration = self.meta.pendingSetattrDuration

            self.apply(args(name, value, annotation), start=start, duration=duration)
        else:
            object.__setattr__(self, name, value)

    def timedSetattr(self, name: str, value: Any, *, start: defaultable[sec] = default(0), duration: defaultable[sec] = default(1)):
        oldPendingSetattrStart = self.meta.pendingSetattrStart
        oldPendingSetattrDuration = self.meta.pendingSetattrDuration
        oldSetattrCallbackOn = self.meta.setattrCallbackOn

        self.meta.pendingSetattrStart = start
        self.meta.pendingSetattrDuration = duration
        self.meta.setattrCallbackOn = True

        try:
            setattr(self, name, value)
        finally:
            self.meta.pendingSetattrStart = oldPendingSetattrStart
            self.meta.pendingSetattrDuration = oldPendingSetattrDuration
            self.meta.setattrCallbackOn = oldSetattrCallbackOn

    def easeTo(self, to: Any, attributeName: str, *, easing=Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        annotation = self.__class__.__annotations__.get(attributeName)
        src = self.__getattribute__(attributeName)
        dst = to

        def _apply(m: number, i: int):
            val = src + (dst - src) * m
            self.timedSetattr(attributeName, val, start=start + i * SF, duration=0)

        animate(duration, easing, _apply)
        return self

    def easeBy(self, by: Any, attributeName: str, *, easing=Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        annotation = self.__class__.__annotations__.get(attributeName)
        src = self.__getattribute__(attributeName)
        dst = src + by

        def _apply(m: number, i: int):
            val = src + (dst - src) * m
            self.timedSetattr(attributeName, val, start=start + i * SF, duration=0)

        animate(duration, easing, _apply)
        return self

    def easeTimes(self, times: Any, attributeName: str, *, easing=Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        annotation = self.__class__.__annotations__.get(attributeName)
        src = self.__getattribute__(attributeName)
        dst = src * times

        def _apply(m: number, i: int):
            val = src + (dst - src) * m
            self.timedSetattr(attributeName, val, start=start + i * SF, duration=0)

        animate(duration, easing, _apply)
        return self

    def __str__(self) -> str:
        s = f"\n{self.__class__.__name__}:\n"
        for k, v in self.__dict__.items():
            s += f"\t{k}={v}\n"
        return s

    def __repr__(self) -> str:
        return self.__str__()

    ### Transformations ###

    def position(self, x: maybe[wint | wfloat] = None, y: maybe[wint | wfloat] = None) -> Self:
        return self.apply(position(x, y))

    def scale(self, factor: maybe[number] = None, *, x: maybe[number] = None, y: maybe[number] = None) -> Self:
        if factor is not None:
            x = factor
            y = factor
        return self.apply(scale(x=x, y=y))

    def rotate(self, degree: number) -> Self:
        return self.apply(rotate(degree))

    def opacity(self, o: number) -> Self:
        return self.apply(opacity(o))

    def align(self, x: maybe[number] = None, y: maybe[number] = None) -> Self:
        return self.apply(align(x, y))

    def hide(self, start: sec = 0):
        return self.apply(hide(), start=start)

    def show(self, start: sec = 0):
        return self.apply(show(), start=start)

    ### Template ###

    def moveTo(self, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        moveTo(self, x=x, y=y, easing=easing, start=start, duration=duration)
        return self

    def moveBy(self, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        moveBy(self, x=x, y=y, easing=easing, start=start, duration=duration)
        return self

    def fadeIn(self, *, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        fadeIn(self, easing=easing, start=start, duration=duration)
        return self

    def fadeOut(self, *, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4, hide=False) -> Self:
        fadeOut(self, easing=easing, start=start, duration=duration)
        if hide:
            return self.hide(start + duration)
        return self

    def scaleTo(self, factor: maybe[number] = None, *, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        if factor is not None:
            x = factor
            y = factor
        scaleTo(self, x=x, y=y, easing=easing, start=start, duration=duration)
        return self

    def scaleBy(self, factor: maybe[number] = None, *, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        if factor is not None:
            x = factor
            y = factor
        scaleBy(self, x=x, y=y, easing=easing, start=start, duration=duration)
        return self
