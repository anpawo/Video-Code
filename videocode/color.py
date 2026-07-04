#!/usr/bin/env python3

from __future__ import annotations

#
# Colors & gradients
#

from typing import cast, overload

type uint8 = int
type unumber = int | float
type degree = unumber
type percent = unumber


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
        if type(other) is not rgba:
            return NotImplemented
        return rgba(self.r + other.r, self.g + other.g, self.b + other.b, self.a + other.a)

    def __sub__(self, other: rgba) -> rgba:
        if type(other) is not rgba:
            return NotImplemented
        return rgba(self.r - other.r, self.g - other.g, self.b - other.b, self.a - other.a)

    def __mul__(self, other: unumber) -> rgba:
        return rgba(
            min(int(self.r * other), 255),
            min(int(self.g * other), 255),
            min(int(self.b * other), 255),
            min(int(self.a * other), 255),
        )

    def __rmul__(self, other: unumber) -> rgba:
        return self.__mul__(other)

    def __eq__(self, other: object) -> bool:
        if type(self) is not rgba or type(other) is not rgba:
            return NotImplemented
        return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a

    def __hash__(self) -> int:
        return hash((self.r, self.g, self.b, self.a))


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
    is_explicit: list[bool] = []
    for stop in stops:
        if isinstance(stop, tuple):
            color, position = stop
            colors.append(color)
            positions.append(float(position))
            is_explicit.append(True)
        else:
            colors.append(stop)
            positions.append(None)
            is_explicit.append(False)

    if positions[0] is None:
        positions[0] = 0.0
    if positions[-1] is None:
        if len(positions) > 1 and all(is_explicit[:-1]):
            # "Fill the rest" — every preceding stop is pinned; the last bare stop
            # fills to 100%.  For the 2-stop wipe pattern (one explicit, one fill-rest):
            #   LinearGradient((RED, p), BLUE)
            # a fixed BLEND_WIDTH blend zone is inserted so BLUE fills solidly from
            # (p+BLEND)% onward — otherwise the gradient runs RED→BLUE all the way from
            # p% to 100%, making RED visually dominant far past p%:
            #   [RED@0%, RED@p%, BLUE@(p+BLEND)%, BLUE@100%]
            # At p=0:   [RED@0%, BLUE@BLEND%, BLUE@100%]   — almost all BLUE
            # At p=50:  [RED@0%, RED@50%, BLUE@70%, BLUE@100%] — clear left/right split
            # At p=100: [RED@0%, RED@100%, BLUE@100%, BLUE@100%] — all RED
            positions[-1] = 100.0
            if len(colors) == 2:
                _BLEND_WIDTH = 20.0
                # blend collapses to 0 at p=0 and p=100, peaks at BLEND_WIDTH in the middle
                blend_zone = min(positions[0], _BLEND_WIDTH, 100.0 - positions[0])
                blend_half = blend_zone / 2
                blend_start = max(0.0, positions[0] - blend_half)
                blend_end = min(100.0, positions[0] + blend_half)
                positions[0] = blend_start  # center the blend zone on p
                colors.append(colors[-1])
                positions.insert(-1, blend_end)
                is_explicit.insert(-1, True)
            if positions[0] > 0.0:
                colors.insert(0, colors[0])
                positions.insert(0, 0.0)
                is_explicit.insert(0, True)
        else:
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
        p_start = cast(float, positions[start])
        p_end = cast(float, positions[end])
        span = p_end - p_start
        for k in range(start + 1, end):
            positions[k] = p_start + span * (k - start) / (end - start)
        i = end + 1

    resolved = cast(list[float], positions)
    for i in range(1, len(resolved)):
        if resolved[i] < resolved[i - 1]:
            resolved[i] = resolved[i - 1]

    return list(zip(colors, resolved))


def _lerpColor(a: rgba, b: rgba, t: float) -> rgba:
    return rgba(
        round(a.r + (b.r - a.r) * t),
        round(a.g + (b.g - a.g) * t),
        round(a.b + (b.b - a.b) * t),
        round(a.a + (b.a - a.a) * t),
    )


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
        solid = self._solidColor()
        if solid is not None:
            return solid.jsonSerialization()
        return (
            [(color.jsonSerialization(), position) for color, position in self.stops],
            self.angle,
        )

    def _solidColor(self) -> rgba | None:
        """Returns the single color if the gradient is effectively solid (all non-zero-width strips share one color), else None."""
        result: rgba | None = None
        for (c0, p0), (c1, p1) in zip(self.stops, self.stops[1:]):
            if p1 <= p0:
                continue
            if c0 != c1:
                return None
            if result is not None and result != c0:
                return None
            result = c0
        return result

    def __str__(self) -> str:
        stopsStr = ", ".join(f"{color}@{position:g}%" for color, position in self.stops)
        return f"LinearGradient({stopsStr}, angle={self.angle})"

    def __repr__(self) -> str:
        return str(self)

    def _promote(self, color: rgba) -> LinearGradient:
        return LinearGradient(*((color, pos) for _, pos in self.stops), angle=self.angle)

    def __or__(self, other: rgba | unumber) -> LinearGradient:
        return LinearGradient(*((color | other, position) for color, position in self.stops), angle=self.angle)

    def __add__(self, other: LinearGradient | rgba) -> LinearGradient:
        if type(other) is rgba:
            return self.__add__(self._promote(other))
        g = cast(LinearGradient, other)
        if len(self.stops) != len(g.stops):
            raise ValueError("LinearGradient addition requires gradients with the same number of stops")
        return LinearGradient(*((c1 + c2, p1) for (c1, p1), (c2, _) in zip(self.stops, g.stops)), angle=self.angle)

    def __radd__(self, other: rgba) -> LinearGradient:
        if type(other) is not rgba:
            return NotImplemented
        return self._promote(other).__add__(self)

    def __sub__(self, other: LinearGradient | rgba) -> LinearGradient:
        if type(other) is rgba:
            return self.__sub__(self._promote(other))
        g = cast(LinearGradient, other)
        if len(self.stops) != len(g.stops):
            raise ValueError("LinearGradient subtraction requires gradients with the same number of stops")
        return LinearGradient(*((c1 - c2, p1) for (c1, p1), (c2, _) in zip(self.stops, g.stops)), angle=self.angle)

    def __rsub__(self, other: rgba) -> LinearGradient:
        if type(other) is not rgba:
            return NotImplemented
        return self._promote(other).__sub__(self)

    def __mul__(self, other: unumber) -> LinearGradient:
        return LinearGradient(*((color * other, position) for color, position in self.stops), angle=self.angle)

    def __rmul__(self, other: unumber) -> LinearGradient:
        return self.__mul__(other)

    def colorAt(self, t: percent) -> rgba:
        """Color at position `t` (0-100%), clamped to the stop range."""
        stops = self.stops
        if t <= stops[0][1]:
            return stops[0][0]
        if t >= stops[-1][1]:
            return stops[-1][0]
        for (c0, p0), (c1, p1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                return _lerpColor(c0, c1, 0.0 if p1 == p0 else (t - p0) / (p1 - p0))
        return stops[-1][0]

    def slice(self, t0: percent, t1: percent) -> LinearGradient:
        """
        Returns the portion of this gradient spanning `[t0, t1]` (0-100%),
        remapped to `[0, 100]` — used to give each letter of a `Text` its own
        slice of a gradient that spans the whole word.
        """
        if t1 - t0 < 1e-9:
            color = self.colorAt(t0)
            return LinearGradient(color, color, angle=self.angle)
        newStops: list[rgba | tuple[rgba, percent]] = [(self.colorAt(t0), 0.0)]
        for color, pos in self.stops:
            if t0 < pos < t1:
                newStops.append((color, (pos - t0) / (t1 - t0) * 100))
        newStops.append((self.colorAt(t1), 100.0))
        return LinearGradient(*newStops, angle=self.angle)


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
