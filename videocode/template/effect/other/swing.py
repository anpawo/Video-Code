#!/usr/bin/env python3

from __future__ import annotations

import math

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.rotate import rotation as _rotation
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def swing(
    *,
    angle: number = 15,
    frequency: number = 3,
    start: sec = 0,
    duration: sec = 1.0,
) -> Effect:
    """
    Pendulum swing: the target rotates back and forth around its center,
    the oscillation decaying to rest — Animate.css's "swing", the angular
    cousin of `shake()`.

    - `angle`: peak deflection in degrees.
    - `frequency`: full swings per second.

        sign.apply(swing())
        bell.apply(swing(angle=25, frequency=4))
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        base = input.meta.rotation
        n = max(int(duration * FRAMERATE), 2)
        for i in range(n):
            t = i / (n - 1)
            if i == n - 1:
                yield _rotation(base).at(start=start + i * SINGLE_FRAME)
                continue
            deflection = angle * math.sin(2 * math.pi * frequency * t * duration) * (1.0 - t)
            yield _rotation(base + deflection).at(start=start + i * SINGLE_FRAME)

    return _apply
