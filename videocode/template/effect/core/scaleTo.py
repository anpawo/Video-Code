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
    about: maybe[v2] = None,
) -> Generator[scale, Any, None]:
    src = v2(*input.meta.scale)
    dst = v2(Maybe(x) | src.x, Maybe(y) | src.y)
    # Only the axis the caller named is CLAIMED — the other travels as `None`, so
    # one axis cannot overwrite an animation on the other that shares its frames.
    for s, i in easing.rangeIdx(src, dst, duration):
        yield scale(s.x if x is not None else None, s.y if y is not None else None, about=about).at(start=start + i * SINGLE_FRAME)


def scaleBy(
    input: Input,
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
    about: maybe[v2] = None,
) -> Generator[scale, Any, None]:
    src = v2(*input.meta.scale)
    dst = v2((Maybe(x) | 0) + src.x, (Maybe(y) | 0) + src.y)
    # Only the axis the caller named is CLAIMED — the other travels as `None`, so
    # one axis cannot overwrite an animation on the other that shares its frames.
    for s, i in easing.rangeIdx(src, dst, duration):
        yield scale(s.x if x is not None else None, s.y if y is not None else None, about=about).at(start=start + i * SINGLE_FRAME)
