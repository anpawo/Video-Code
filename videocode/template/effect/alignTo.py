#!/usr/bin/env python3


from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.shader.vertexShader.align import align
from videocode.utils.bezier import *


if TYPE_CHECKING:
    from videocode.input.input import Input


def alignTo(input: Input, x: maybe[wnumber], y: maybe[wnumber], *, easing: easing = Easing.Linear, start: sec = 0, duration: sec = 0.4) -> None:
    src = v2(*input.meta.align)
    dst = v2(Maybe(x) | src.x, Maybe(y) | src.y)

    def apply(m: number, i: int):
        px = src.x + (dst.x - src.x) * m
        py = src.y + (dst.y - src.y) * m
        input.apply(align(x=px, y=py), start=i * SF)

    animate(duration, easing, apply)
