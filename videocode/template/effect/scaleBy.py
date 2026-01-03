#!/usr/bin/env python3


from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.shader.vertexShader.scale import scale
from videocode.utils.bezier import *


if TYPE_CHECKING:
    from videocode.input.input import Input


def scaleBy(input: Input, x: maybe[number] = None, y: maybe[number] = None, *, easing: easing = Easing.Linear, start: sec = 0, duration: sec = 0.4) -> None:
    src = input.meta.scale
    dst = v2(src.x + (0 if x is None else x), src.y + (0 if y is None else y))

    def apply(m: number, i: int):
        sx = src.x + (dst.x - src.x) * m
        sy = src.y + (dst.y - src.y) * m
        input.apply(scale(x=sx, y=sy), start=i * SF)

    animate(start, duration, easing, apply)
