#!/usr/bin/env python3


from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.vertexShader.opacity import opacity
from videocode.utils.bezier import *
from videocode.utils.classutils import Maybe


if TYPE_CHECKING:
    from videocode.input.input import Input


def fadeTo(
    input: "Input",
    *,
    src: maybe[unumber] = None,
    dst: unumber,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.Linear,
) -> Generator[opacity, Any, None]:
    src_val = Maybe(src) | input.meta.opacity
    for o, i in easing.rangeIdx(src_val, dst, duration):
        yield opacity(o).at(start=start + i * SINGLE_FRAME)
