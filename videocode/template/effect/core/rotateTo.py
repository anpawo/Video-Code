#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import VertexShader
from videocode.shader.vertexShader.rotate import rotation
from videocode.utils.bezier import *


if TYPE_CHECKING:
    from videocode.input.input import Input


def rotateTo(
    input: Input,
    dst: unumber,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[rotation, Any, None]:
    src = input.meta.rotation
    for o, i in easing.rangeIdx(src, dst, duration):
        yield rotation(o).at(start=start + i * SINGLE_FRAME)


def rotateBy(
    input: Input,
    dst: unumber,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[rotation, Any, None]:
    src = input.meta.rotation
    for o, i in easing.rangeIdx(src, src + dst, duration):
        yield rotation(o).at(start=start + i * SINGLE_FRAME)
