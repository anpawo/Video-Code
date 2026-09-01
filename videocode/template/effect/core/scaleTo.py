#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.vertexShader.position import position
from videocode.shader.vertexShader.scale import scale
from videocode.utils.bezier import *
from videocode.utils.classutils import Maybe


if TYPE_CHECKING:
    from videocode.input.input import Input


def _spread(input: Input, about: maybe[v2], src: v2):
    """
    A leaf scaled about a point moves away from (or toward) it.

    Same shape as `rotateTo._orbit`, and the same capability question: a group
    resolves `about` itself in `_emitRigid`. An axis the caller did not claim
    keeps its factor at 1, so scaling x alone does not drag the leaf along y.
    """
    if about is None or getattr(input, "_memberBases", None) is not None:
        return None

    at0 = v2(*input.meta.position)
    rx, ry = at0.x - about.x, at0.y - about.y

    def at(now: v2) -> position:
        fx = now.x / src.x if src.x else 1.0
        fy = now.y / src.y if src.y else 1.0
        return position(rx * fx + about.x, ry * fy + about.y)

    return at


def scaleTo(
    input: Input,
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
    about: maybe[v2] = None,
) -> Generator[scale | position, Any, None]:
    src = v2(*input.meta.scale)
    dst = v2(Maybe(x) | src.x, Maybe(y) | src.y)
    # Only the axis the caller named is CLAIMED — the other travels as `None`, so
    # one axis cannot overwrite an animation on the other that shares its frames.
    spread = _spread(input, about, src)
    for s, i in easing.rangeIdx(src, dst, duration):
        t = start + i * SINGLE_FRAME
        yield scale(s.x if x is not None else None, s.y if y is not None else None, about=about).at(start=t)
        if spread is not None:
            yield spread(v2(s.x if x is not None else src.x, s.y if y is not None else src.y)).at(start=t)


def scaleBy(
    input: Input,
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
    about: maybe[v2] = None,
) -> Generator[scale | position, Any, None]:
    src = v2(*input.meta.scale)
    dst = v2((Maybe(x) | 0) + src.x, (Maybe(y) | 0) + src.y)
    # Only the axis the caller named is CLAIMED — the other travels as `None`, so
    # one axis cannot overwrite an animation on the other that shares its frames.
    spread = _spread(input, about, src)
    for s, i in easing.rangeIdx(src, dst, duration):
        t = start + i * SINGLE_FRAME
        yield scale(s.x if x is not None else None, s.y if y is not None else None, about=about).at(start=t)
        if spread is not None:
            yield spread(v2(s.x if x is not None else src.x, s.y if y is not None else src.y)).at(start=t)
