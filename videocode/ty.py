#!/usr/bin/env python3

from __future__ import annotations

#
# Types
#

from typing import TYPE_CHECKING, Any, Generic, Literal, Protocol, Self, cast, overload

from videocode.color import ConicGradient, LinearGradient, RadialGradient, rgba

if TYPE_CHECKING:
    # Only for the lazily-evaluated `paint` alias below — a runtime import
    # would be circular (ishader -> constants -> ty).
    from videocode.shader.ishader import PaintShader


type int8 = int

type uint = int
type uint8 = int
type ufloat = float

# world unit
type wint = int
type wuint = int
type wfloat = float
type wufloat = float
type wnumber = float | int
type wunumber = float | int


type sec = ufloat | uint
type frame = uint
"""
is in frame count not sec
"""

type maybe[T] = T | None

type paint = rgba | PaintShader
"""
what fillColor accepts: a color (incl. gradients) or a PaintShader — a
fragment shader that GENERATES pixels (silk/fire/starNest/mathShader), as
opposed to the filter kind (blur/grayscale/...) which only transforms
existing pixels and belongs in .apply(). PEP 695 aliases evaluate lazily,
so the TYPE_CHECKING-only PaintShader import is enough.
"""
type number = int | float
type unumber = int | float
type mnbr = maybe[number]
"""
shorthand for `maybe[number]`
"""

type degree = number
type index = int
type url = str
type percent = number

type point = tuple[wnumber, wnumber]

type attrName = str | Any


class v2[XT: maybe[number], YT: maybe[number]]:
    """
    Vector 2D
    """

    def __init__(self, x: XT, y: YT) -> None:
        self.x: XT = x
        self.y: YT = y

    def __add__(self, other: v2) -> v2:
        x = self.x + other.x if (self.x is not None and other.x is not None) else (self.x if self.x is not None else other.x)
        y = self.y + other.y if (self.y is not None and other.y is not None) else (self.y if self.y is not None else other.y)
        return v2(x, y)

    def __sub__(self, other: v2) -> v2:
        x = self.x - other.x if (self.x is not None and other.x is not None) else (self.x if self.x is not None else other.x)
        y = self.y - other.y if (self.y is not None and other.y is not None) else (self.y if self.y is not None else other.y)
        return v2(x, y)

    def __mul__(self, m: number) -> v2:
        x = self.x * m if self.x is not None else self.x
        y = self.y * m if self.y is not None else self.y
        return v2(x, y)

    def __div__(self, d: number) -> v2:
        x = self.x / d if self.x is not None else self.x
        y = self.y / d if self.y is not None else self.y
        return v2(x, y)

    def __iter__(self):
        yield self.x
        yield self.y

    def jsonSerialization(self):
        return vars(self)

    def __str__(self) -> str:
        return f"{{x: {self.x}, y: {self.y}}}"

    def __repr__(self) -> str:
        return str(self)


class Arithmetic(Protocol):
    """
    Supports basic arithmetic operations.
    """

    def __add__(self, other: Self, /) -> Self: ...
    def __sub__(self, other: Self, /) -> Self: ...
    def __mul__(self, other: number, /) -> Self: ...
