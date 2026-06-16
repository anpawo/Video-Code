#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.utils.bezier import *
from videocode.shader.vertexShader.position import position
from videocode.shader.vertexShader.translate import translate
from videocode.utils.classutils import Maybe


if TYPE_CHECKING:
    from videocode.input.input import Input
    from videocode.input.interface.Group import Group


def moveTo(
    input: "Input",
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[position, Any, None]:
    src = v2(*input.meta.position)
    dst = v2(Maybe(x) | src.x, Maybe(y) | src.y)
    for p, i in easing.rangeIdx(src, dst, duration):
        yield position(*p).at(start=start + i * SINGLE_FRAME)


def moveBy(
    input: "Input",
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[position, Any, None]:
    src = v2(*input.meta.position)
    dst = v2(src.x + (Maybe(x) | 0), src.y + (Maybe(y) | 0))
    for p, i in easing.rangeIdx(src, dst, duration):
        yield position(*p).at(start=start + i * SINGLE_FRAME)


def groupMoveBy(
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[translate, Any, None]:
    """
    Shift every member of a `Group` by the same `(x, y)` delta, preserving
    their relative layout — unlike `moveBy`, which would collapse the group
    to a single absolute position.
    """
    src = v2(0, 0)
    dst = v2(Maybe(x) | 0, Maybe(y) | 0)
    prev = src
    for p, i in easing.rangeIdx(src, dst, duration):
        yield translate(p.x - prev.x, p.y - prev.y).at(start=start + i * SINGLE_FRAME)
        prev = p


def groupMoveTo(
    group: "Group[Any]",
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[translate, Any, None]:
    """
    Move a `Group` so the centroid of its members' positions lands at
    `(x, y)`, preserving their relative layout — see `groupMoveBy`.
    """
    positions: list[v2[wnumber, wnumber]] = []
    group.broadcast(lambda i: positions.append(v2(*i.meta.position)))

    if not positions:
        yield from groupMoveBy(x=x, y=y, start=start, duration=duration, easing=easing)
        return

    center = v2(
        sum(p.x for p in positions) / len(positions),
        sum(p.y for p in positions) / len(positions),
    )
    dx = (Maybe(x) | center.x) - center.x
    dy = (Maybe(y) | center.y) - center.y
    yield from groupMoveBy(x=dx, y=dy, start=start, duration=duration, easing=easing)
