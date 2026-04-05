#!/usr/bin/env python3


from typing import TYPE_CHECKING, Callable
from videocode.constants import FRAMERATE, number
from videocode.ty import sec


if TYPE_CHECKING:
    from videocode.input.input import Input


class _BezierRange:
    def __init__(self, bezier: "cubicBezier", start: number, end: number, n: int):
        self.bezier = bezier
        self.start = start
        self.end = end
        self.n = n
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self) -> float:
        if self.i >= self.n:
            raise StopIteration
        t = self.i / (self.n - 1) if self.n > 1 else 0.0
        val = self.start + self.bezier(t) * (self.end - self.start)
        self.i += 1
        return val


class cubicBezier:
    def __init__(
        self,
        #
        x1: number,
        y1: number,
        x2: number,
        y2: number,
    ) -> None:
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def bezier(self, t, p0, p1, p2, p3):
        return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3

    def derivative(self, t, p0, p1, p2, p3):
        return 3 * (1 - t) ** 2 * (p1 - p0) + 6 * (1 - t) * t * (p2 - p1) + 3 * t**2 * (p3 - p2)

    def solveTForX(self, x):
        """
        Newton-Raphson
        """
        t = x
        for _ in range(8):
            x_t = self.bezier(t, 0, self.x1, self.x2, 1)
            dx_dt = self.derivative(t, 0, self.x1, self.x2, 1)
            if dx_dt == 0:
                break
            t -= (x_t - x) / dx_dt
            t = max(0, min(t, 1))
        return t

    def getValueAtX(self, x: float):
        t = self.solveTForX(x)
        return self.bezier(t, 0, self.y1, self.y2, 1)

    def __call__(self, x: float) -> float:
        return self.getValueAtX(x)

    def range(self, start: number, end: number, duration: sec):
        n = int(duration * FRAMERATE)
        return _BezierRange(self, start, end, n)


class Easing:
    Linear = cubicBezier(0.0, 0.0, 1.0, 1.0)
    In = cubicBezier(0.42, 0.0, 1.0, 1.0)
    Out = cubicBezier(0.0, 0.0, 0.58, 1.0)
    InOut = cubicBezier(0.42, 0.0, 0.58, 1.0)


type easing = cubicBezier


def animate(start: sec, duration: sec, easing: easing, apply: Callable[[number, int], None]):
    n = int((duration - start) * FRAMERATE)

    for i in range(n):
        t = i / (n - 1)
        m = easing(t)
        apply(m, i)
