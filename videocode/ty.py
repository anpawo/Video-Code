#!/usr/bin/env python3

#
# Types
#

from typing import Any, Generic, Protocol, Self, TypeVar, cast, overload


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

    def jsonSerialization(self):
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


def _normalizeStops(
    stops: tuple[rgba | tuple[rgba, percent], ...],
) -> list[tuple[rgba, float]]:
    """
    Resolves a mix of bare colors (auto-positioned) and `(color, percent)` pairs
    (pinned) into a fully-positioned stop list, mirroring CSS color-stop layout:
    the first/last stop default to 0%/100% when unpositioned, runs of unpositioned
    stops are spaced evenly between their positioned neighbors, and positions are
    clamped to be monotonically non-decreasing.
    """
    if len(stops) < 2:
        raise ValueError("LinearGradient/RadialGradient needs at least 2 color stops")

    colors: list[rgba] = []
    positions: list[float | None] = []
    for stop in stops:
        if isinstance(stop, tuple):
            color, position = stop
            colors.append(color)
            positions.append(float(position))
        else:
            colors.append(stop)
            positions.append(None)

    if positions[0] is None:
        positions[0] = 0.0
    if positions[-1] is None:
        positions[-1] = 100.0

    i = 1
    while i < len(positions):
        if positions[i] is not None:
            i += 1
            continue
        start = i - 1
        end = i + 1
        while positions[end] is None:
            end += 1
        span = positions[end] - positions[start]
        for k in range(start + 1, end):
            positions[k] = positions[start] + span * (k - start) / (end - start)
        i = end + 1

    resolved = cast(list[float], positions)
    for i in range(1, len(resolved)):
        if resolved[i] < resolved[i - 1]:
            resolved[i] = resolved[i - 1]

    return list(zip(colors, resolved))


class LinearGradient(rgba):
    """
    An `rgba` that fills a shape with a linear gradient across multiple color
    stops, oriented by `angle` (0 = left → right, 90 = bottom → top).

    Stops are bare colors (auto-positioned — evenly spaced between their
    positioned neighbors, with the first/last defaulting to 0%/100%) or
    `(color, percent)` pairs that pin a stop at an exact position — exactly
    like CSS `linear-gradient(red 0%, yellow 30%, blue 100%)`:

        LinearGradient(RED, BLUE)                        # RED@0%, BLUE@100%
        LinearGradient(RED, (GREEN, 30), BLUE, angle=90) # GREEN pinned at 30%
        LinearGradient(RED, (GREEN, 50), BLUE, WHITE)    # BLUE auto-spaced to ~75%
    """

    def __init__(self, *stops: rgba | tuple[rgba, percent], angle: degree = 0):
        self.stops = _normalizeStops(stops)
        self.angle = angle

    def jsonSerialization(self):
        return (
            [(color.jsonSerialization(), position) for color, position in self.stops],
            self.angle,
        )

    def __str__(self) -> str:
        stopsStr = ", ".join(f"{color}@{position:g}%" for color, position in self.stops)
        return f"LinearGradient({stopsStr}, angle={self.angle})"

    def __repr__(self) -> str:
        return str(self)

    def __or__(self, other: rgba | unumber) -> LinearGradient:
        return LinearGradient(*((color | other, position) for color, position in self.stops), angle=self.angle)

    def __add__(self, other: rgba) -> LinearGradient:
        return LinearGradient(*((color + other, position) for color, position in self.stops), angle=self.angle)

    def __sub__(self, other: rgba) -> LinearGradient:
        return LinearGradient(*((color - other, position) for color, position in self.stops), angle=self.angle)

    def __mul__(self, other: unumber) -> LinearGradient:
        return LinearGradient(*((color * other, position) for color, position in self.stops), angle=self.angle)

    def __rmul__(self, other: unumber) -> LinearGradient:
        return self.__mul__(other)


class RadialGradient(rgba):
    """
    An `rgba` that fills a shape with a radial gradient — color varies by
    distance from the shape's center outward, like CSS `radial-gradient`.

    Stops follow the same `(color, percent)` / bare-color convention as
    `LinearGradient`, where 0% = center and 100% = farthest point of the shape:

        RadialGradient(RED, BLUE)               # RED at center, BLUE at edge
        RadialGradient(RED, (WHITE, 30), BLUE)  # WHITE ring at 30% radius
    """

    def __init__(self, *stops: rgba | tuple[rgba, percent]):
        self.stops = _normalizeStops(stops)

    def jsonSerialization(self):
        return (
            [(color.jsonSerialization(), position) for color, position in self.stops],
            "radial",
        )

    def __str__(self) -> str:
        stopsStr = ", ".join(f"{color}@{position:g}%" for color, position in self.stops)
        return f"RadialGradient({stopsStr})"

    def __repr__(self) -> str:
        return str(self)

    def __or__(self, other: rgba | unumber) -> RadialGradient:
        return RadialGradient(*((color | other, position) for color, position in self.stops))

    def __add__(self, other: rgba) -> RadialGradient:
        return RadialGradient(*((color + other, position) for color, position in self.stops))

    def __sub__(self, other: rgba) -> RadialGradient:
        return RadialGradient(*((color - other, position) for color, position in self.stops))

    def __mul__(self, other: unumber) -> RadialGradient:
        return RadialGradient(*((color * other, position) for color, position in self.stops))

    def __rmul__(self, other: unumber) -> RadialGradient:
        return self.__mul__(other)


class ConicGradient(rgba):
    """
    An `rgba` that fills a shape with a conic gradient — color sweeps around
    the shape's center, like CSS `conic-gradient`.

    Stops follow the same `(color, percent)` / bare-color convention as
    `LinearGradient`/`RadialGradient`: 0% = `angle`, 100% = one full
    counterclockwise revolution back to `angle` (same convention as
    LinearGradient's `angle`: 0° = right, 90° = up). If the first and last
    stop colors differ, a hard seam appears at `angle`:

        ConicGradient(RED, BLUE)                  # seam at angle: BLUE meets RED
        ConicGradient(RED, (WHITE, 50), BLUE, angle=90)
    """

    def __init__(self, *stops: rgba | tuple[rgba, percent], angle: degree = 0):
        self.stops = _normalizeStops(stops)
        self.angle = angle

    def jsonSerialization(self):
        return (
            [(color.jsonSerialization(), position) for color, position in self.stops],
            ("conic", self.angle),
        )

    def __str__(self) -> str:
        stopsStr = ", ".join(f"{color}@{position:g}%" for color, position in self.stops)
        return f"ConicGradient({stopsStr}, angle={self.angle})"

    def __repr__(self) -> str:
        return str(self)

    def __or__(self, other: rgba | unumber) -> ConicGradient:
        return ConicGradient(*((color | other, position) for color, position in self.stops), angle=self.angle)

    def __add__(self, other: rgba) -> ConicGradient:
        return ConicGradient(*((color + other, position) for color, position in self.stops), angle=self.angle)

    def __sub__(self, other: rgba) -> ConicGradient:
        return ConicGradient(*((color - other, position) for color, position in self.stops), angle=self.angle)

    def __mul__(self, other: unumber) -> ConicGradient:
        return ConicGradient(*((color * other, position) for color, position in self.stops), angle=self.angle)

    def __rmul__(self, other: unumber) -> ConicGradient:
        return self.__mul__(other)


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
