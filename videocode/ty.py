#!/usr/bin/env python3

#
# Types
#

# alias
from typing import Any, overload
from typing_extensions import Self


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
type frame = int
"""
is in frame count not sec
"""

type maybe[T] = T | None
type number = int | float
type unumber = int | float

type degree = float
type index = int
type url = str
type percent = number

type point = tuple[wnumber, wnumber]

type attrName = str | Any


class rgba:
    @overload
    def __init__(self, r: uint8 = 0, g: uint8 = 0, b: uint8 = 0, a: uint8 = 255): ...

    @overload
    def __init__(self, r: str = "#000000"): ...

    def __init__(self, r: uint8 | str = 0, g: uint8 = 0, b: uint8 = 0, a: uint8 = 255):
        if isinstance(r, str):
            h = r.lstrip("#")
            self.r = int(h[0:2], 16)
            self.g = int(h[2:4], 16)
            self.b = int(h[4:6], 16)
            self.a = int(h[6:8], 16) if len(h) == 8 else 255
        else:
            self.r = r
            self.g = g
            self.b = b
            self.a = a

    def makeSerializable(self):
        return (self.r, self.g, self.b, self.a)

    def __str__(self) -> str:
        return f"({self.r}, {self.g}, {self.b}, {self.a})"

    def __repr__(self) -> str:
        return str(self)

    def __or__(self, other: rgba | unumber) -> rgba:
        if isinstance(other, rgba):
            return rgba(
                (self.r + other.r) // 2,
                (self.g + other.g) // 2,
                (self.b + other.b) // 2,
                (self.a + other.a) // 2,
            )
        return rgba(self.r, self.g, self.b, int(self.a * other))

    def __add__(self, other: rgba) -> rgba:
        return rgba(
            self.r + other.r,
            self.g + other.g,
            self.b + other.b,
            self.a + other.a,
        )

    def __sub__(self, other: rgba) -> rgba:
        return rgba(
            self.r - other.r,
            self.g - other.g,
            self.b - other.b,
            self.a - other.a,
        )

    def __mul__(self, other: unumber) -> rgba:
        return rgba(
            min(int(self.r * other), 255),
            min(int(self.g * other), 255),
            min(int(self.b * other), 255),
            min(int(self.a * other), 255),
        )

    def __rmul__(self, other: unumber) -> rgba:
        return self.__mul__(other)


# vector 2D
class v2[T]:
    x: T
    y: T

    def __iter__(self):
        yield self.x
        yield self.y

    def __init__(self, x: T, y: T) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: v2[maybe[number]]) -> v2:
        x = self.x + other.x if isinstance(self.x, int | float) and isinstance(other.x, int | float) else self.x if self.x is not None else other.x
        y = self.y + other.y if isinstance(self.y, int | float) and isinstance(other.y, int | float) else self.y if self.y is not None else other.y
        return v2(x, y)

    def __sub__(self, other: v2[maybe[number]]) -> v2:
        x = self.x - other.x if isinstance(self.x, int | float) and isinstance(other.x, int | float) else self.x if self.x is not None else other.x
        y = self.y - other.y if isinstance(self.y, int | float) and isinstance(other.y, int | float) else self.y if self.y is not None else other.y
        return v2(x, y)

    def __mul__(self, m: number) -> v2:
        x = self.x * m if isinstance(self.x, int | float) else self.x
        y = self.y * m if isinstance(self.y, int | float) else self.y
        return v2(x, y)

    def __div__(self, d: number) -> v2:
        x = self.x / d if isinstance(self.x, int | float) else self.x
        y = self.y / d if isinstance(self.y, int | float) else self.y
        return v2(x, y)

    def makeSerializable(self):
        return {"x": self.x, "y": self.y}

    def __str__(self) -> str:
        return f"{{x: {self.x}, y: {self.y}}}"

    def __repr__(self) -> str:
        return str(self)
