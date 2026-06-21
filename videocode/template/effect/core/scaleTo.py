#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.vertexShader.scale import scale
from videocode.utils.bezier import *
from videocode.utils.classutils import Maybe


if TYPE_CHECKING:
    from videocode.input.input import Input


def scaleTo(
    input: Input,
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
    input: Input,
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[scale, Any, None]:
    src = v2(*input.meta.scale)
    dst = v2((Maybe(x) | 0) + src.x, (Maybe(y) | 0) + src.y)
    for s, i in easing.rangeIdx(src, dst, duration):
        yield scale(*s).at(start=start + i * SINGLE_FRAME)
