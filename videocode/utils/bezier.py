#!/usr/bin/env python3

from __future__ import annotations

import math

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Generator, overload
from videocode.constants import FRAMERATE, number
from videocode.ty import Arithmetic, sec, index


if TYPE_CHECKING:
    from videocode.input.input import Input


class RateFunc(ABC):
    """
    A function `t in [0, 1] -> m` mapping animation progress to interpolation
    weight, used by `range`/`rangeIdx` as `start + (end - start) * self(t)`.
    """

    @abstractmethod
    def __call__(self, t: float) -> float: ...

    @overload
    def range(self, start: int, end: int, duration: sec) -> Generator[float, Any, None]: ...
    @overload
    def range[T: Arithmetic](self, start: T, end: T, duration: sec) -> Generator[T, Any, None]: ...
    def range(self, start: Any, end: Any, duration: sec) -> Generator[Any, Any, None]:
        n = int(duration * FRAMERATE)
        for i in range(0, n):
            t = i / (n - 1) if n > 1 else 0.0
            yield start + (end - start) * self(t)

    @overload
    def rangeIdx(self, start: int, end: int, duration: sec) -> Generator[tuple[float, index], Any, None]: ...
    @overload
    def rangeIdx[T: Arithmetic](self, start: T, end: T, duration: sec) -> Generator[tuple[T, index], Any, None]: ...
    def rangeIdx(self, start: Any, end: Any, duration: sec) -> Generator[tuple[Any, index], Any, None]:
        n = int(duration * FRAMERATE)
        for i in range(0, n):
            t = i / (n - 1) if n > 1 else 0.0
            yield start + (end - start) * self(t), i


class CubicBezier(RateFunc):
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


class Func(RateFunc):
    """
    Wraps an arbitrary `t in [0, 1] -> m` function as a `RateFunc` —
    used for rate functions that aren't expressible as a `CubicBezier`
    from (0, 0) to (1, 1), e.g. non-monotonic ones like `Easing.ThereAndBack`
    or `Easing.Wiggle`.
    """

    def __init__(self, fn: Callable[[float], float]) -> None:
        self.fn = fn

    def __call__(self, t: float) -> float:
        return self.fn(t)


def _smooth(t: float, inflection: float = 10.0) -> float:
    """Manim's sigmoid-based `smooth` rate function."""
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    error = 1 / (1 + math.exp(inflection / 2))
    raw = 1 / (1 + math.exp(-inflection * (t - 0.5)))
    return min(max((raw - error) / (1 - 2 * error), 0.0), 1.0)


def _rushInto(t: float) -> float:
    return 2 * _smooth(t / 2)


def _rushFrom(t: float) -> float:
    return 2 * _smooth(t / 2 + 0.5) - 1


def _slowInto(t: float) -> float:
    return math.sqrt(1 - (1 - t) ** 2)


def _doubleSmooth(t: float) -> float:
    if t < 0.5:
        return 0.5 * _smooth(2 * t)
    return 0.5 * (1 + _smooth(2 * t - 1))


def _thereAndBack(t: float) -> float:
    return _smooth(2 * t if t < 0.5 else 2 * (1 - t))


def _thereAndBackWithPause(t: float, pauseRatio: float = 1 / 3) -> float:
    a = 1 / pauseRatio
    if t < 0.5 - pauseRatio / 2:
        return _smooth(a * t)
    if t > 0.5 + pauseRatio / 2:
        return _smooth(a - a * t)
    return 1.0


def _wiggle(t: float) -> float:
    return _thereAndBack(t) * math.sin(2 * math.pi * t)


def _exponentialDecay(t: float, halfLife: float = 0.1) -> float:
    return 1 - math.exp(-t / halfLife)


class Easing:
    Linear = CubicBezier(0.0, 0.0, 1.0, 1.0)
    In = CubicBezier(0.42, 0.0, 1.0, 1.0)
    Out = CubicBezier(0.0, 0.0, 0.58, 1.0)
    InOut = CubicBezier(0.42, 0.0, 0.58, 1.0)

    # Manim-inspired rate functions (`videocode.utils.bezier`'s ported
    # equivalents of manim's `rate_functions` module). `ThereAndBack`,
    # `ThereAndBackWithPause` and `Wiggle` deliberately end back at `t=0`
    # (not `t=1`) — used with `range`/`rangeIdx`'s `start + (end-start)*self(t)`,
    # they animate out and back to the start value.
    Smooth = Func(_smooth)
    RushInto = Func(_rushInto)
    RushFrom = Func(_rushFrom)
    SlowInto = Func(_slowInto)
    DoubleSmooth = Func(_doubleSmooth)
    ThereAndBack = Func(_thereAndBack)
    ThereAndBackWithPause = Func(_thereAndBackWithPause)
    Wiggle = Func(_wiggle)
    ExponentialDecay = Func(_exponentialDecay)


type easing = RateFunc


def animate(duration: sec, easing: easing, apply: Callable[[number, int], None]):
    n = int(duration * FRAMERATE)

    for i in range(n):
        t = i / (n - 1)
        m = easing(t)
        apply(m, i)
