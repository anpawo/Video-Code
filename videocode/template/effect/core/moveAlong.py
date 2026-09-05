#!/usr/bin/env python3

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Generator, Sequence

from videocode.constants import *
from videocode.shader.vertexShader.position import position
from videocode.shader.vertexShader.rotate import rotation
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def _walk(points: Sequence[tuple[number, number]]) -> tuple[list[v2], list[float]]:
    """
    The path as points, and how far along it each one stands.

    Travelling a polyline by its POINTS is not travelling it at all: the points
    a curve is written with are dense where it bends and sparse where it runs
    straight, so an object stepping from one to the next crawls through the
    corners and bolts down the straights. What an author means by "go along
    this" is a constant speed, and constant speed is distance, so the walk is
    measured before anything moves.
    """
    walked = [v2(float(p[0]), float(p[1])) for p in points]
    lengths = [0.0]
    for before, after in zip(walked, walked[1:]):
        step = math.hypot(after.x - before.x, after.y - before.y)
        lengths.append(lengths[-1] + step)
    return walked, lengths


def _at(walked: list[v2], lengths: list[float], distance: float) -> v2:
    """Where the path stands `distance` along itself."""
    if distance <= 0 or lengths[-1] == 0:
        return walked[0]
    if distance >= lengths[-1]:
        return walked[-1]

    for i in range(1, len(lengths)):
        if lengths[i] < distance:
            continue
        span = lengths[i] - lengths[i - 1]
        share = 0.0 if span == 0 else (distance - lengths[i - 1]) / span
        before, after = walked[i - 1], walked[i]
        return v2(before.x + (after.x - before.x) * share, before.y + (after.y - before.y) * share)
    return walked[-1]


def moveAlong(
    input: Input,
    path: Any,
    *,
    start: sec = 0,
    duration: sec = 1.2,
    easing: easing = Easing.InOut,
    face: bool = False,
) -> Generator[Any, Any, None]:
    """
    Travel a path at an even speed, optionally turned the way it is going.

    `path` is a `Curve` — or anything with `vertices`, or a plain list of
    points. The path is measured first and walked by DISTANCE, so a curve whose
    points crowd around its bends is still crossed at one speed; `easing`
    then shapes that speed as it shapes any other animation.

    `face=True` also turns the element to point along the path. The angle is
    read from where it has just been to where it is going, which is the only
    direction a path can be said to have, and the last frame keeps the angle of
    the one before it rather than snapping back to zero.
    """
    points = getattr(path, "vertices", path)
    if len(points) < 2:
        raise ValueError("moveAlong needs a path of at least two points")

    walked, lengths = _walk(points)
    if lengths[-1] == 0:
        raise ValueError("moveAlong was given a path of no length — every point is the same one")

    n = max(1, int(duration * FRAMERATE))
    places = [_at(walked, lengths, easing(i / (n - 1) if n > 1 else 1.0) * lengths[-1]) for i in range(n)]

    facing = 0.0
    for i, here in enumerate(places):
        yield position(here.x, here.y).at(start=start + i * SINGLE_FRAME)

        if face:
            # The direction is read from the frame before to the frame after —
            # a path has no direction at a single point, and the ends borrow
            # the step they have. A frame that does not move keeps the angle it
            # had rather than snapping back to zero.
            before = places[i - 1] if i else here
            after = places[i + 1] if i + 1 < n else here
            dx, dy = after.x - before.x, after.y - before.y
            if dx or dy:
                # A positive degree turns clockwise on screen — the rotation is
                # applied in pixel space, which is Y-flipped against the world.
                facing = -math.degrees(math.atan2(dy, dx))
            yield rotation(facing).at(start=start + i * SINGLE_FRAME)
