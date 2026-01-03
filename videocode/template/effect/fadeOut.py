#!/usr/bin/env python3


from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.shader.fragmentShader.opacity import opacity
from videocode.utils.bezier import *


if TYPE_CHECKING:
    from videocode.input.input import Input


def fadeOut(input: Input, *, easing: easing = Easing.Linear, start: sec = 0, duration: sec = 0.4) -> None:
    src: unumber = 255
    dst: unumber = 0

    def apply(m: number, i: int):
        o = src + (dst - src) * m
        input.apply(opacity(opacity=o), start=i * SINGLE_FRAME, duration=SINGLE_FRAME)

    animate(start, duration, easing, apply)
