#!/usr/bin/env python3


from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.shader.vertexShader.position import position
from videocode.utils.bezier import cubicBezier, Easing, easing, animate


if TYPE_CHECKING:
    from videocode.input.Input import Input


def moveBy(input: Input, x: maybe[number] = None, y: maybe[number] = None, *, easing: easing = Easing.Linear, start: sec = 0, duration: sec = 0.4) -> None:
    src = input.meta.position
    dst = v2(src.x + (0 if x is None else x), src.y + (0 if y is None else y))

    def apply(m: number, i: int):
        px = src.x + (dst.x - src.x) * m
        py = src.y + (dst.y - src.y) * m
        input.apply(position(x=px, y=py), start=i * SF)

    animate(start, duration, easing, apply)
