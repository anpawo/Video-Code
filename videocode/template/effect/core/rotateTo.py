#!/usr/bin/env python3

from __future__ import annotations

import math

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import VertexShader
from videocode.shader.vertexShader.position import position
from videocode.shader.vertexShader.rotate import rotation
from videocode.utils.bezier import *


if TYPE_CHECKING:
    from videocode.input.input import Input


def _orbit(input: Input, about: maybe[v2], src: number):
    """
    A leaf turning about a point has to travel: nothing downstream will move it.

    A group resolves `about` itself in `_emitRigid`, orbiting each member from
    its frozen base — asked here as a capability (does it hold member bases?)
    rather than as a class, because that is the question being asked. Returns a
    function of the angle, or None when there is nothing to orbit.

    The turn is negated for the reason `_emitRigid` negates it: C++ renders a
    positive degree as a clockwise spin, the rotation matrix living in pixel
    space, which is Y-flipped against world space.
    """
    if about is None or getattr(input, "_memberBases", None) is not None:
        return None

    start = v2(*input.meta.position)
    rx, ry = start.x - about.x, start.y - about.y

    def at(degree: number) -> position:
        rad = math.radians(-(degree - src))
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        return position(rx * cos_r - ry * sin_r + about.x, rx * sin_r + ry * cos_r + about.y)

    return at


def rotateTo(
    input: Input,
    dst: unumber,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
    about: maybe[v2] = None,
) -> Generator[rotation | position, Any, None]:
    src = input.meta.rotation
    orbit = _orbit(input, about, src)
    for o, i in easing.rangeIdx(src, dst, duration):
        t = start + i * SINGLE_FRAME
        yield rotation(o, about=about).at(start=t)
        if orbit is not None:
            yield orbit(o).at(start=t)


def rotateBy(
    input: Input,
    dst: unumber,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
    about: maybe[v2] = None,
) -> Generator[rotation | position, Any, None]:
    src = input.meta.rotation
    orbit = _orbit(input, about, src)
    for o, i in easing.rangeIdx(src, src + dst, duration):
        t = start + i * SINGLE_FRAME
        yield rotation(o, about=about).at(start=t)
        if orbit is not None:
            yield orbit(o).at(start=t)
