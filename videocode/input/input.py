#!/usr/bin/env python3


from __future__ import annotations
from copy import deepcopy
from abc import ABC, abstractmethod
from functools import singledispatchmethod
from typing import Any, Callable, Self, cast
from videocode.template.effect.align import alignTo
from videocode.template.effect.fade import fadeTo
from videocode.template.effect.move import moveTo, moveBy
from videocode.template.effect.rotate import rotateBy, rotateTo
from videocode.template.effect.scale import scaleBy, scaleTo
from videocode.shader.ishader import DeferredShader, IShader, VertexShader
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
from videocode.utils.classutils import At, AttributeNameReference, Maybe


class Input(ABC):
    """
    An `Input` is a source that you want to add to the timeline of the video.

    It can be an `Image`, a `Video`, a `Shape`, some `Text` etc...
    """

    cppName: str = "Input"
    """
    Cpp Name of the Input.
    """

    cppAttrs: set[str] = set()
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
    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self: ...

    @overload
    def apply(self, *shaders: tuple[IShader, sec, sec]) -> Self: ...

    @singledispatchmethod
    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        """
        Applies some `Transformations` to the `Input`.

        The `duration` is in `seconds`, so it will affect `duration * framerate` frames of the video.
        """

        # If a `wait()` happens, any input should be flushed before applying any new effect.
        if Context.waitOffset >= self.meta.transformationOffset:
            self.waitTo(Context.waitOffset)

        # Do not modify the initial shaders.
        for s in deepcopy(shaders):
            # Deferred shaders produce other smaller shaders
            if isinstance(s, DeferredShader):
                self.apply(*s.resolve(self))
                continue

            # Normal shader produce other smaller shaders
            __start = int(start * FRAMERATE) + Maybe(offset).orElse(self.meta.transformationOffset)
            __duration = int((s.duration if hasattr(s, "duration") else duration) * FRAMERATE)

            # Update lastEverAffectedFrame
            if Context.lastEverAffectedFrame < __start + __duration:
                Context.lastEverAffectedFrame = __start + __duration

            # Update our lastAffectedFrame
            if __start + __duration > self.meta.lastAffectedFrame:
                self.meta.lastAffectedFrame = __start + __duration

            # Transformations affect the Input's Metadata
            if isinstance(s, VertexShader):
                if s.autodestroy(self):
                    continue
                else:
                    s.modify(self)

            # Args w/ Start & Duration
            args = vars(s) | {"start": __start, "duration": __duration}

            # Add step to the stack
            Context.apply(self.meta.index, upperFirst(s.__class__.__name__), s._type, args)

            # Callbacks
            for callback in self.meta.callbacks.get(type(s), []):
                callback(s, start, duration, Maybe(offset).orElse(self.meta.transformationOffset))

        return self

    @apply.register(tuple)
    def _(self, *shaders: tuple[IShader, sec, sec]):  # TODO: add transformationOffset
        for s, start, duration in deepcopy(shaders):
            self.apply(s, start=start, duration=duration)
        return self

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Handles attributes updates.

        __setattr__ has priority over __set__.
        """
        # Use object.__getattribute__ to bypass Intefaces's broadcast mechanism — # Old comment to keep for information purpose.

        if type(value) == At:
            value, start, duration, offset = value.unpack()
            if hasattr(self, name) and name in self.cppAttrs:
                if not getattr(self, name) == value:
                    self.apply(args(name, value), start=start, duration=duration, offset=offset)
            else:
                # property side effects
                old = self.meta.pendingStart, self.meta.pendingDuration, self.meta.pendingOffset
                new = start, duration, offset

                self.meta.pendingStart, self.meta.pendingDuration, self.meta.pendingOffset = new

                def pendingOn(i: Input):
                    i.meta.pendingStart, i.meta.pendingDuration, i.meta.pendingOffset = new

                def pendingOff(i: Input):
                    i.meta.pendingStart, i.meta.pendingDuration, i.meta.pendingOffset = old

                self.broadcast(pendingOn)
                try:
                    setattr(self, name, value)
                finally:
                    self.meta.pendingStart, self.meta.pendingDuration, self.meta.pendingOffset = old
                    self.broadcast(pendingOff)
        elif hasattr(self, name) and name in self.cppAttrs:
            if not getattr(self, name) == value:
                self.apply(args(name, value), start=self.meta.pendingStart, duration=self.meta.pendingDuration, offset=self.meta.pendingOffset)
        else:
            object.__setattr__(self, name, value)

    def broadcast(self, func: Callable[[Input], Any]):
        """
        Broadcast a method through potential children that the Input might have or itself.

        Will be overriden by Interfaces.
        """
        func(self)

    def ease(
        self,
        attr: attrName,
        to: Any,
        *,
        easing=Easing.InOut,
        start: sec = 0,
        duration: sec = 0.4,
        offset: maybe[frame] = None,
    ) -> Self:
        src = self.__getattribute__(attr)

        def _apply(m: number, i: int):
            setattr(self, attr, At(start=start + i * SF, duration=SINGLE_FRAME, offset=offset) | (src + (to - src) * m))

        animate(duration, easing, _apply)
        return self

    def easeTogether(
        self,
        *anims: tuple[attrName, Any] | tuple[attrName, Any, CubicBezier],
        easing=Easing.InOut,
        start: sec = 0,
        duration: sec = 0.4,
        offset: maybe[frame] = None,
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
                m = easingFunc(t)
                setattr(self, attr, At(start=start + i * SF, duration=SINGLE_FRAME, offset=offset) | (src + (to - src) * m))

        return self

    @property
    def ref(self) -> Self:
        """
        Reference to prevent string missmatch
        """
        return cast(Self, AttributeNameReference(self))

    def addCallback[T: IShader](self, shaderType: type[T], callback: Callable[[T, sec, sec, frame], None]) -> None:
        """
        Track an Input's Shaders and react by doing something else.
        """
        cb = cast(Callable[[IShader, sec, sec, frame], None], callback)
        if self.meta.callbacks.get(shaderType) is None:
            self.meta.callbacks[shaderType] = [cb]
        else:
            self.meta.callbacks[shaderType].append(cb)

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
        return self.apply(moveTo(x=x, y=y, easing=easing, start=start, duration=duration))

    def moveBy(self, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(moveBy(x=x, y=y, easing=easing, start=start, duration=duration))

    def fadeIn(self, *, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4, from0: maybe[bool] = True) -> Self:
        return self.apply(fadeTo(src=0 if from0 else None, dst=255, easing=easing, start=start, duration=duration))

    def fadeOut(self, *, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4, hide=False, from255: maybe[bool] = True) -> Self:
        self.apply(fadeTo(src=255 if from255 else None, dst=0, easing=easing, start=start, duration=duration))
        if hide:
            return self.hide(start=start + duration)
        return self

    def scaleTo(self, factor: maybe[number] = None, *, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        if factor is not None:
            x = factor
            y = factor
        return self.apply(scaleTo(x=x, y=y, easing=easing, start=start, duration=duration))

    def scaleBy(self, factor: maybe[number] = None, *, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        if factor is not None:
            x = factor
            y = factor
        return self.apply(scaleBy(x=x, y=y, easing=easing, start=start, duration=duration))

    def rotateTo(self, degree: number, *, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(rotateTo(dst=degree, easing=easing, start=start, duration=duration))

    def rotateBy(self, degree: number, *, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(rotateBy(dst=degree, easing=easing, start=start, duration=duration))

    def alignTo(self, x: maybe[number] = None, y: maybe[number] = None, easing: CubicBezier = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(alignTo(x=x, y=y, easing=easing, start=start, duration=duration))
