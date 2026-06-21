#!/usr/bin/env python3


from __future__ import annotations
from copy import copy as _shallow_copy
from abc import ABC, abstractmethod
from typing import Any, Callable, Self, cast
from videocode.template.effect.core.alignTo import alignTo
from videocode.template.effect.core.fadeTo import fadeTo
from videocode.template.effect.core.moveTo import moveTo, moveBy
from videocode.template.effect.core.rotateTo import rotateBy, rotateTo
from videocode.template.effect.core.scaleTo import scaleBy, scaleTo
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
from videocode.shader.vertexShader.translate import translate
from videocode.shader.vertexShader.show import show
from videocode.shader.vertexShader.opacity import opacity
from videocode.shader.vertexShader.zIndex import zIndex
from videocode.utils.bezier import animate, Easing, easing
from videocode.utils.logger import *
from videocode.utils.classutils import At, AttributeNameReference


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

    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        """
        Applies some `Transformations` to the `Input`.

        The `duration` is in `seconds`, so it will affect `duration * framerate` frames of the video.
        """

        # If a `wait()` happens, any input should be flushed before applying any new effect.
        if Context.waitOffset >= self.meta.transformationOffset:
            self.waitTo(Context.waitOffset)

        for s in shaders:
            # Pre-callbacks: fire before resolve/modify/stack-push. Mutate shader fields to rewrite
            # values, or return True to drop the shader entirely. Return False to let it through.
            if any(
                cb(s, start, duration, offset if offset is not None else self.meta.transformationOffset)
                for cb in self.meta.preCallbacks.get(type(s), [])
            ):
                continue

            _s, _d, _o = s.resolve(start, duration, offset)

            __start = round(_s * FRAMERATE) + (_o if _o is not None else self.meta.transformationOffset)
            __duration = round(_d * FRAMERATE)
            __end = __start + __duration

            # Update lastEverAffectedFrame
            if Context.lastEverAffectedFrame < __end:
                Context.lastEverAffectedFrame = __end

            # Update our lastAffectedFrame
            if __end > self.meta.lastAffectedFrame:
                self.meta.lastAffectedFrame = __end

            # Transformations affect the Input's Metadata.
            # VertexShader.modify() writes resolved values back to self.* (e.g. position.modify
            # sets self.x = current x when x=None) so vars(s) contains the right args.
            # Shallow copy is sufficient: only primitive attributes are reassigned, never mutated.
            # FragmentShaders never mutate self, so no copy is needed there.
            # autodestroy() only reads from self (the Input), never mutates s — safe to check
            # before copying so no-op shaders skip the allocation entirely.
            if isinstance(s, VertexShader):
                if s.autodestroy(self):
                    continue
                s = _shallow_copy(s)
                s.modify(self)

            # Args w/ Start & Duration
            args = {k: v for k, v in vars(s).items() if k not in ("start", "duration", "offset")} | {"start": __start, "duration": __duration}

            # Add step to the stack
            Context.apply(self.meta.index, upperFirst(s.__class__.__name__), s._type, args)

            # Post-callbacks
            for callback in self.meta.postCallbacks.get(type(s), []):
                callback(s, start, duration, offset if offset is not None else self.meta.transformationOffset)

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
                    self.apply(args(name, value).at(start=start, duration=duration, offset=offset))
            else:
                # property side effects
                old = self.meta.pendingStart, self.meta.pendingDuration, self.meta.pendingOffset
                new = start, duration, offset

                def pendingOn(i: Input):
                    i.meta.pendingStart, i.meta.pendingDuration, i.meta.pendingOffset = new

                def pendingOff(i: Input):
                    i.meta.pendingStart, i.meta.pendingDuration, i.meta.pendingOffset = old

                self.broadcast(pendingOn)
                try:
                    setattr(self, name, value)
                finally:
                    self.broadcast(pendingOff)
        elif hasattr(self, name) and name in self.cppAttrs:
            if not getattr(self, name) == value:
                self.apply(args(name, value).at(start=self.meta.pendingStart, duration=self.meta.pendingDuration, offset=self.meta.pendingOffset))
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
        *anims: tuple[attrName, Any] | tuple[attrName, Any, easing],
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

    def addPreCallback[T: IShader](self, shaderType: type[T], callback: Callable[[T, sec, sec, frame], bool]) -> None:
        """
        Register a pre-callback for a shader type. Called before Context.apply; return True to skip the shader.
        """
        cb = cast(Callable[[IShader, sec, sec, frame], bool], callback)
        self.meta.preCallbacks.setdefault(shaderType, []).append(cb)

    def addPostCallback[T: IShader](self, shaderType: type[T], callback: Callable[[T, sec, sec, frame], None]) -> None:
        """
        Track an Input's Shaders and react by doing something else.
        """
        cb = cast(Callable[[IShader, sec, sec, frame], None], callback)
        self.meta.postCallbacks.setdefault(shaderType, []).append(cb)

    def __str__(self) -> str:
        s = f"{self.__class__.__name__}"
        return s

    def __repr__(self) -> str:
        return self.__str__()

    @property
    @abstractmethod
    def width(self) -> wnumber: ...

    @property
    @abstractmethod
    def height(self) -> wnumber: ...

    def animateIn(self) -> Self:
        return self

    ### Transformations ###

    def position(self, x: maybe[wnumber] = None, y: maybe[wnumber] = None, *, offset: maybe[frame] = None) -> Self:
        return self.apply(position(x, y), offset=offset)

    def translate(self, x: maybe[number] = None, y: maybe[number] = None, *, offset: maybe[frame] = None) -> Self:
        return self.apply(translate(x, y), offset=offset)

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

    def zIndex(self, z: int) -> Self:
        return self.apply(zIndex(z))

    def inFrontOf(self, other: Input) -> Self:
        """
        Render directly in front of `other`.
        """
        return self.zIndex(other.meta.zIndex)

    def behind(self, other: Input) -> Self:
        """
        Render directly behind `other`.
        """
        return self.zIndex(other.meta.zIndex - 1)

    def bringToFront(self) -> Self:
        """
        Render in front of every other `Input` in the scene.
        """
        return self.zIndex(Context.maxZIndex())

    def sendToBack(self) -> Self:
        """
        Render behind every other `Input` in the scene.
        """
        # Clamped to 0: zIndex -1 is reserved for the background
        # (see BACKGROUND_Z_INDEX / Input.background()).
        return self.zIndex(max(0, Context.minZIndex() - 1))

    def bringForward(self) -> Self:
        """
        Move one layer towards the front, swapping places with whatever is
        directly in front. No-op if already frontmost.
        """
        above = Context.zIndexAbove(self.meta.zIndex)
        if above is None:
            return self
        return self.zIndex(above)

    def sendBackward(self) -> Self:
        """
        Move one layer towards the back, swapping places with whatever is
        directly behind. No-op if already backmost.
        """
        below = Context.zIndexBelow(self.meta.zIndex)
        if below is None:
            return self
        # Clamped to 0: zIndex -1 is reserved for the background
        # (see BACKGROUND_Z_INDEX / Input.background()).
        return self.zIndex(max(0, below - 1))

    def background(self) -> Self:
        """
        Mark this `Input` (and any children) as part of the scene background:
        sets `zIndex` to `BACKGROUND_Z_INDEX` (-1).

        Excluded from relative layer-order queries (bringToFront, sendToBack,
        bringForward, sendBackward), so they never get pushed behind/in front
        of the background by accident. Relative order between background
        elements (e.g. Plane's grid lines on top of its backdrop rectangle)
        is preserved by zOrderSeq, since they all tie at -1.
        """
        self.broadcast(lambda i: i.zIndex(BACKGROUND_Z_INDEX))
        return self

    def hide(self, start: sec = 0):
        return self.apply(hide().at(start=start))

    def show(self, start: sec = 0):
        return self.apply(show().at(start=start))

    ### Template ###

    def moveTo(self, x: maybe[number] = None, y: maybe[number] = None, easing: easing = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(*moveTo(self, x=x, y=y, easing=easing, start=start, duration=duration))

    def moveBy(self, x: maybe[number] = None, y: maybe[number] = None, easing: easing = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(*moveBy(self, x=x, y=y, easing=easing, start=start, duration=duration))

    def fadeIn(self, *, easing: easing = Easing.InOut, start: sec = 0, duration: sec = 0.4, from0: maybe[bool] = True) -> Self:
        return self.apply(*fadeTo(self, src=0 if from0 else None, dst=255, easing=easing, start=start, duration=duration))

    def fadeOut(self, *, easing: easing = Easing.InOut, start: sec = 0, duration: sec = 0.4, hide=False, from255: maybe[bool] = True) -> Self:
        self.apply(*fadeTo(self, src=255 if from255 else None, dst=0, easing=easing, start=start, duration=duration))
        if hide:
            return self.hide(start=start + duration)
        return self

    def scaleTo(
        self,
        factor: maybe[number] = None,
        *,
        x: maybe[number] = None,
        y: maybe[number] = None,
        easing: easing = Easing.InOut,
        start: sec = 0,
        duration: sec = 0.4,
    ) -> Self:
        if factor is not None:
            x = factor
            y = factor
        return self.apply(*scaleTo(self, x=x, y=y, easing=easing, start=start, duration=duration))

    def scaleBy(
        self,
        factor: maybe[number] = None,
        *,
        x: maybe[number] = None,
        y: maybe[number] = None,
        easing: easing = Easing.InOut,
        start: sec = 0,
        duration: sec = 0.4,
    ) -> Self:
        if factor is not None:
            x = factor
            y = factor
        return self.apply(*scaleBy(self, x=x, y=y, easing=easing, start=start, duration=duration))

    def rotateTo(self, degree: number, *, easing: easing = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(*rotateTo(self, dst=degree, easing=easing, start=start, duration=duration))

    def rotateBy(self, degree: number, *, easing: easing = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(*rotateBy(self, dst=degree, easing=easing, start=start, duration=duration))

    def alignTo(self, x: maybe[number] = None, y: maybe[number] = None, easing: easing = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(*alignTo(self, x=x, y=y, easing=easing, start=start, duration=duration))
