#!/usr/bin/env python3


import math


from videocode.input.input import *
from videocode.input.interface.Interface import Interface
from videocode.shader.vertexShader.position import position
from videocode.shader.vertexShader.rotate import rotation
from videocode.shader.vertexShader.scale import scale
from videocode.utils.decorators import prop


class Offset[T: Input](Interface):
    """
    Wraps an input with a fixed local-frame offset `(x, y)` and rotation delta `r`.

    The offset is expressed in the input's local coordinate frame: positive `x` moves
    along the input's forward direction, positive `y` moves perpendicular (up at 0°).
    When the input rotates, the offset rotates with it.
    """

    def __init__(self, i: T, x: wnumber = 0, y: wnumber = 0, r: wnumber = 0):  # TODO: scale too
        self.input: T = i
        self.xOffset = x
        self.yOffset = y
        self.rOffset = r
        self.meta.position = v2(*i.meta.position)
        self.meta.rotation = i.meta.rotation
        self._sync(start=0, duration=SINGLE_FRAME, offset=None)

    def _syncPending(self):
        self._sync(
            start=self.input.meta.pendingStart,
            duration=self.input.meta.pendingDuration,
            offset=self.input.meta.pendingOffset,
        )

    @prop(onSet=_syncPending)
    def xOffset() -> wnumber: ...

    @prop(onSet=_syncPending)
    def yOffset() -> wnumber: ...

    @prop(onSet=_syncPending)
    def rOffset() -> wnumber: ...

    def broadcast(self, func: Callable[[Input], Any]):
        self.input.broadcast(func)

    def _sync(self, *, start: sec, duration: sec, offset: maybe[frame]):
        angle = math.radians(self.meta.rotation)
        lx = self.xOffset * self.input.meta.scale.x
        ly = -self.yOffset * self.input.meta.scale.y  # negate: user +y = up, trig needs -ly
        wx = self.meta.position.x + lx * math.cos(angle) - ly * math.sin(angle)
        wy = self.meta.position.y - lx * math.sin(angle) - ly * math.cos(angle)
        self.input.apply(
            position(wx, wy),
            rotation(self.meta.rotation + self.rOffset),
            start=start,
            duration=duration,
            offset=offset,
        )

    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        for s in shaders:
            _s, _d, _o = s.resolve(start, duration, offset)

            if isinstance(s, position):
                if s.x is not None:
                    self.meta.position.x = s.x
                if s.y is not None:
                    self.meta.position.y = s.y
                self._sync(start=_s, duration=_d, offset=_o)
            elif isinstance(s, rotation):
                self.meta.rotation = s.degree
                self._sync(start=_s, duration=_d, offset=_o)
            elif isinstance(s, scale):
                self.input.apply(s, start=_s, duration=_d, offset=_o)
                self._sync(start=_s, duration=_d, offset=_o)
            else:
                self.input.apply(s, start=_s, duration=_d, offset=_o)

        return self

    def __str__(self) -> str:
        s = f"{self.__class__.__name__}({self.input}, x={self.xOffset}, y={self.yOffset})"
        return s

    def __repr__(self) -> str:
        return self.__str__()
