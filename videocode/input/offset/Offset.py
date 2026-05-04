#!/usr/bin/env python3


import math


from videocode.input.input import *
from videocode.shader.vertexShader.position import position
from videocode.shader.vertexShader.rotate import rotation
from videocode.shader.vertexShader.scale import scale


class Offset[T: Input](Input):
    """
    Wraps an input with a fixed local-frame offset `(x, y)` and rotation delta `r`.

    The offset is expressed in the input's local coordinate frame: positive `x` moves
    along the input's forward direction, positive `y` moves perpendicular (up at 0°).
    When the input rotates, the offset rotates with it.
    """

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.meta = Metadata(interface=True)
        return instance

    def __init__(self, i: T, x: wnumber = 0, y: wnumber = 0, r: wnumber = 0):
        self.input: T = i
        self.x = x
        self.y = y
        self.r = r
        self._basePosition = v2(*i.meta.position)
        self._baseRotation = i.meta.rotation
        self._sync(start=0, duration=0)

    def _sync(self, *, start: sec, duration: sec):
        angle = math.radians(self._baseRotation)
        lx = self.x * self.input.meta.scale.x
        ly = -self.y * self.input.meta.scale.y  # negate: user +y = up, trig needs -ly
        wx = self._basePosition.x + lx * math.cos(angle) - ly * math.sin(angle)
        wy = self._basePosition.y - lx * math.sin(angle) - ly * math.cos(angle)
        self.input.apply(
            position(wx, wy),
            rotation(self._baseRotation + self.r),
            start=start,
            duration=duration,
        )

    def flush(self) -> Self:
        self.input.flush()
        return self

    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = 1) -> Self:
        needs_sync = False

        for s in shaders:
            if isinstance(s, position):
                if s.x is not None:
                    self._basePosition.x = s.x
                    self.meta.position.x = s.x
                if s.y is not None:
                    self._basePosition.y = s.y
                    self.meta.position.y = s.y
                needs_sync = True
            elif isinstance(s, rotation):
                self._baseRotation = s.degree
                needs_sync = True
            elif isinstance(s, scale):
                self.input.apply(s, start=start, duration=duration)
                needs_sync = True
            else:
                self.input.apply(s, start=start, duration=duration)

        if needs_sync:
            self._sync(start=start, duration=duration)

        return self

    def __str__(self) -> str:
        return f"\nOffset ({self.x}, {self.y}, r+{self.r}):\n{self.input}"

    def __repr__(self) -> str:
        return self.__str__()
