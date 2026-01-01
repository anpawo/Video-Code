#!/usr/bin/env python3


from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.effect.shader.opacity import opacity
from videocode.utils.bezier import *
from videocode.effect.transformation.position import position


if TYPE_CHECKING:
    from videocode.input.input import Input


def fadeIn(input: Input, *, easing: easing = Easing.Linear, start: sec = 0, duration: sec = 0.4) -> None:
    src: unumber = 0
    dst: unumber = 255

    def apply(m: number, i: int):
        o = src + (dst - src) * m
        input.apply(opacity(opacity=o), start=i * SINGLE_FRAME)

    animate(start, duration, easing, apply)
