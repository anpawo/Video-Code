#!/usr/bin/env python3


from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.vertexShader.align import align
from videocode.utils.bezier import *
from videocode.utils.classutils import Maybe


if TYPE_CHECKING:
    from videocode.input.input import Input


def alignTo(
    input: "Input",
    x: maybe[wnumber] = None,
    y: maybe[wnumber] = None,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[align, Any, None]:
    src = v2(input.meta.align.x, input.meta.align.y)
    dst = v2(Maybe(x) | src.x, Maybe(y) | src.y)

    for a, i in easing.rangeIdx(src, dst, duration):
        yield align(*a).at(start=start + i * SINGLE_FRAME)
