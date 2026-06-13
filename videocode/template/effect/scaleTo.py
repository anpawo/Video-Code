#!/usr/bin/env python3


from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.vertexShader.scale import scale
from videocode.shader.vertexShader.scaleDelta import scaleDelta
from videocode.utils.bezier import *
from videocode.utils.classutils import Maybe


if TYPE_CHECKING:
    from videocode.input.input import Input
    from videocode.input.interface.Group import Group


def scaleTo(
    input: "Input",
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[scale, Any, None]:
    src = v2(*input.meta.scale)
    dst = v2(Maybe(x) | src.x, Maybe(y) | src.y)
    for s, i in easing.rangeIdx(src, dst, duration):
        yield scale(*s).at(start=start + i * SINGLE_FRAME)


def scaleBy(
    input: "Input",
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[scale, Any, None]:
    src = v2(*input.meta.scale)
    dst = v2(Maybe(x) | 0 + src.x, Maybe(y) | 0 + src.y)
    for s, i in easing.rangeIdx(src, dst, duration):
        yield scale(*s).at(start=start + i * SINGLE_FRAME)


def groupScaleBy(
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[scaleDelta, Any, None]:
    """
    Shift every member of a `Group`'s scale by the same `(x, y)` delta,
    preserving any differences in their scales — unlike `scaleBy`, which would
    collapse the group to a single absolute scale.
    """
    src = v2(0, 0)
    dst = v2(Maybe(x) | 0, Maybe(y) | 0)
    prev = src
    for s, i in easing.rangeIdx(src, dst, duration):
        yield scaleDelta(s.x - prev.x, s.y - prev.y).at(start=start + i * SINGLE_FRAME)
        prev = s


def groupScaleTo(
    group: "Group[Any]",
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[scaleDelta, Any, None]:
    """
    Scale a `Group` so the average of its members' scales reaches `(x, y)`,
    preserving any differences in their scales — see `groupScaleBy`.
    """
    scales: list[v2[wnumber, wnumber]] = []
    group.broadcast(lambda i: scales.append(v2(*i.meta.scale)))

    if not scales:
        yield from groupScaleBy(x=x, y=y, start=start, duration=duration, easing=easing)
        return

    avg = v2(
        sum(s.x for s in scales) / len(scales),
        sum(s.y for s in scales) / len(scales),
    )
    dx = (Maybe(x) | avg.x) - avg.x
    dy = (Maybe(y) | avg.y) - avg.y
    yield from groupScaleBy(x=dx, y=dy, start=start, duration=duration, easing=easing)
