#!/usr/bin/env python3


from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.shader.vertexShader.rotate import rotation
from videocode.utils.bezier import *


if TYPE_CHECKING:
    from videocode.input.input import Input


def rotateTo(input: Input, degree: number, *, easing: easing = Easing.Linear, start: sec = 0, duration: sec = 0.4) -> None:
    src = input.meta.rotation
    dst = degree

    def apply(m: number, i: int):
        d = src + (dst - src) * m
        input.apply(rotation(degree=d), start=i * SF)

    animate(duration, easing, apply)
