#!/usr/bin/env python3

#
# Types
#


# alias
type uint = int
type uint8 = int
type ufloat = float

type wint = int  # world unit
type wuint = int  # world unit
type wfloat = float  # world unit
type wufloat = float  # world unit

type degree = float

type sec = ufloat | uint

type maybe[T] = T | None
type number = int | float
type unumber = int | float

type index = int
type url = str


class rgba:
    def __init__(self, r: uint8, g: uint8, b: uint8, a: uint8) -> None:
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


class default[T]:
    """
    Default value to specify that a value is the default one and should be overriden by a given one.
    """

    def __init__(self, value: T) -> None:
        self.value = value

    def __str__(self) -> str:
        return f"default({self.value})"


type defaultable[T] = default[T] | T
