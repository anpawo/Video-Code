#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.utils.bezier import *
from videocode.shader.vertexShader.position import position
from videocode.utils.classutils import Maybe

if TYPE_CHECKING:
    from videocode.input.input import Input


def moveTo(
    input: Input,
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
    input: Input,
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
