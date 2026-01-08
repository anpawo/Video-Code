#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING

from ...constants import *
from ...shader.fragmentShader.opacity import opacity
from ...utils.bezier import *

if TYPE_CHECKING:
    from ...input.Input import Input


def fadeOut(input: Input, *, easing: easing = Easing.Linear, start: sec = 0, duration: sec = 0.4) -> None:
    src: unumber = 255
    dst: unumber = 0

    def apply(m: number, i: int):
        o = src + (dst - src) * m
        input.apply(opacity(opacity=o), start=i * SINGLE_FRAME, duration=SINGLE_FRAME)

    animate(start, duration, easing, apply)
