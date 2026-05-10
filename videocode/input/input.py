#!/usr/bin/env python3


from __future__ import annotations
from copy import deepcopy
from abc import ABC, abstractmethod
from functools import singledispatchmethod
from typing import Any, Callable, Self, cast
from videocode.template.effect.alignTo import alignTo
from videocode.template.effect.fadeTo import fadeTo
from videocode.template.effect.moveTo import moveTo
from videocode.template.effect.rotateTo import rotateTo
from videocode.template.effect.scaleTo import scaleTo
from videocode.shader.ishader import IShader, VertexShader
from videocode.context import *
from videocode.constants import *
from videocode.utils.funcutils import *
from videocode.shader.vertexShader.align import align
from videocode.shader.vertexShader.args import args
from videocode.shader.vertexShader.hide import hide
from videocode.shader.vertexShader.rotate import rotation
from videocode.shader.vertexShader.scale import scale
from videocode.shader.vertexShader.position import position
from videocode.shader.vertexShader.show import show
from videocode.shader.vertexShader.opacity import opacity
from videocode.utils.bezier import animate, CubicBezier, Easing
from videocode.utils.logger import *
from videocode.utils.classutils import AttributeNameReference, Maybe


class Input(ABC):
    """
    An `Input` is a source that you want to add to the timeline of the video.

    It can be an `Image`, a `Video`, a `Shape`, some `Text` etc...
    """

    cppName: str
    """
    Cpp Name of the Input.
    """

    cppAttrs: set[str]
    """
    Attributes to pass to the cpp.
    """

    meta: Metadata = cast(Metadata, None)
    """
    Metadata of the `Input`.
    """

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
        self.meta.lastAffectedFrame = n
        return self.flush()

    def wait(self, n: sec) -> Self:
        self.meta.lastAffectedFrame += int(n * FRAMERATE)
        return self.flush()

    def waitFor(self, i: Input) -> Self:
        return self.waitTo(i.meta.lastAffectedFrame)

    @overload
    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = 1) -> Self: ...

    @overload
    def apply(self, *shaders: tuple[IShader, sec, sec]) -> Self: ...

    @singledispatchmethod
    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = SINGLE_FRAME) -> Self:
        """
        Applies some `Transformations` to the `Input`.

        The `duration` is in `seconds`, so it will affect `duration * framerate` frames of the video.
        """

        # If a `wait()` happens, any input should be flushed before applying any new effect.
        if Context.waitOffset >= self.meta.transformationOffset:
            self.waitTo(Context.waitOffset)

        # Do not modify the initial shaders.
        for s in deepcopy(shaders):
            __start = int(start * FRAMERATE) + self.meta.transformationOffset
            __duration = int((s.duration if hasattr(s, "duration") else duration) * FRAMERATE)

            # Update lastEverAffectedFrame
            if Context.lastEverAffectedFrame < __start + __duration:
                Context.lastEverAffectedFrame = __start + __duration

            # Update our lastAffectedFrame
            if __start + __duration > self.meta.lastAffectedFrame:
                self.meta.lastAffectedFrame = __start + __duration

            # Transformations affect the Input's Metadata
            if isinstance(s, VertexShader):
                s.modificator(self)

            # Round floats to 6 decimals
            args = {k: round(v, 6) if isinstance(v, float) else v for k, v in vars(s).items()}
            args |= {"start": __start, "duration": __duration}

            # Add step to the stack
            Context.apply(self.meta.index, upperFirst(s.__class__.__name__), s._type, args)

            # Callbacks
            for callback in self.meta.callbacks.get(type(s), []):
                callback(s, __start * SINGLE_FRAME, __duration * SINGLE_FRAME)

        return self

    @apply.register(tuple)
    def _(self, *shaders: tuple[IShader, sec, sec]):
        for s, start, duration in deepcopy(shaders):
            self.apply(s, start=start, duration=duration)
        return self

    ### Builtins ###

    def __enter__(self):
        self.meta.setattrCallbackOn = True
        return self

    def __exit__(self, excType, excValue, traceback):
        self.meta.setattrCallbackOn = False
        return False

    def __setattr__(self, name: str, value: Any) -> None:
        # Modifications should affect the cpp
        if hasattr(self, "meta") and self.meta is not None and self.meta.setattrCallbackOn:
            # attr isnt a property
            if not name in self.meta.props:
                # attr is an attr that the cpp care about
                if name in self.cppAttrs:
                    self.apply(args(name, value), start=self.meta.pendingSetattrStart, duration=self.meta.pendingSetattrDuration)
                    return
        object.__setattr__(self, name, value)

    def set(self, name: attrName, value: Any, *, start: sec = 0, duration: sec = 1):
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

    def ease(self, attributeName: attrName, to: Any, *, easing=Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        src = self.__getattribute__(attributeName)
        dst = to

        def _apply(m: number, indexOffset: int):
            val = src + (dst - src) * m
            self.set(attributeName, val, start=start + indexOffset * SF, duration=0)

        animate(duration, easing, _apply)
        return self

    def easeTogether(
        self,
        *anims: tuple[attrName, Any] | tuple[attrName, Any, CubicBezier],
        easing=Easing.InOut,
        start: sec = 0,
        duration: sec = 0.4,
    ) -> Self:
        n = int(duration * FRAMERATE)

        # Snapshot all sources before scheduling anything
        snapshot = {attr: getattr(self, attr) for (attr, _, *_) in anims}

        for i in range(n):
            t = i / (n - 1)

            for anim in anims:
                attr, to, *rest = anim
                easingFunc = rest[0] if rest else easing

                src = snapshot[attr]
                dst = to
                m = easingFunc(t)
                val = src + (dst - src) * m

                self.set(attr, val, start=start + i * SF, duration=0)

        return self

    @property
    def ref(self) -> Self:
        """
        Reference to prevent string missmatch
        """
        return cast(Self, AttributeNameReference(self))

    def addCallback(self, shaderType: type[IShader], callback: Callable[[IShader, sec, sec], None]) -> None:
        """
        Track an Input's Shaders and react by doing something else.
        """
        if self.meta.callbacks.get(shaderType) is None:
            self.meta.callbacks[shaderType] = [callback]
        else:
            self.meta.callbacks[shaderType].append(callback)

    def __str__(self) -> str:
        s = f"{self.__class__.__name__}"
        return s

    def __repr__(self) -> str:
        return self.__str__()

    ### Transformations ###

    def position(self, x: maybe[wnumber] = None, y: maybe[wnumber] = None) -> Self:
        return self.apply(position(x, y))

    def align(self, x: maybe[wnumber] = None, y: maybe[wnumber] = None) -> Self:
        return self.apply(align(x, y))

    def rotation(self, degree: number) -> Self:
        return self.apply(rotation(degree))

    def scale(self, factor: maybe[number] = None, *, x: maybe[number] = None, y: maybe[number] = None) -> Self:
        if factor is not None:
            x = factor
            y = factor
        return self.apply(scale(x, y))

    def opacity(self, o: number) -> Self:
        return self.apply(opacity(o))

    def hide(self, start: sec = 0):
        return self.apply(hide(), start=start)

    def show(self, start: sec = 0):
        return self.apply(show(), start=start)

    ### Template ###

    def moveTo(self, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        moveTo(self, x=x, y=y, easing=easing, start=start, duration=duration)
        return self

    def moveBy(self, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        p = self.meta.position
        moveTo(
            self,
            x=Maybe(x).map(lambda v: p.x + v).get(),
            y=Maybe(y).map(lambda v: p.y + v).get(),
            easing=easing,
            start=start,
            duration=duration,
        )
        return self

    def fadeIn(self, *, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        fadeTo(self, src=0, dst=255, easing=easing, start=start, duration=duration)
        return self

    def fadeOut(self, *, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4, hide=False) -> Self:
        fadeTo(self, src=255, dst=0, easing=easing, start=start, duration=duration)
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
        s = self.meta.scale
        scaleTo(
            self,
            x=Maybe(x).map(lambda v: s.x + v).get(),
            y=Maybe(y).map(lambda v: s.y + v).get(),
            easing=easing,
            start=start,
            duration=duration,
        )
        return self

    def rotateTo(self, degree: number, *, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        rotateTo(self, degree=degree, easing=easing, start=start, duration=duration)
        return self

    def rotateBy(self, degree: number, *, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        rotateTo(self, degree=self.meta.rotation + degree, easing=easing, start=start, duration=duration)
        return self

    def alignTo(self, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        alignTo(
            self,
            x=Maybe(x) | self.meta.align.x,
            y=Maybe(y) | self.meta.align.y,
            easing=easing,
            start=start,
            duration=duration,
        )
        return self
