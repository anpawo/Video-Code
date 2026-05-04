#!/usr/bin/env python3


from typing import TYPE_CHECKING

from constants import *
from videocode.shader.vertexShader.opacity import opacity
from utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def fadeTo(input: Input, src: unumber, dst: unumber, *, easing: easing = Easing.Linear, start: sec = 0, duration: sec = 0.4) -> None:

    def apply(m: number, i: int):
        o = src + (dst - src) * m
        input.apply(opacity(opacity=o), start=i * SINGLE_FRAME, duration=SINGLE_FRAME)

    animate(duration, easing, apply)
