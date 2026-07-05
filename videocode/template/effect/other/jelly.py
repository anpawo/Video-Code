#!/usr/bin/env python3

from __future__ import annotations

import math

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def jelly(
    *,
    amplitude: number = 0.18,
    frequency: number = 5,
    start: sec = 0,
    duration: sec = 0.8,
) -> Effect:
    """
    Squash & stretch wobble: scale.x and scale.y oscillate in OPPOSITE phase
    (wide-and-flat ↔ tall-and-thin) with a decaying envelope, ending exactly
    at the original scale — the cartoon "jelly" emphasis.

    - `amplitude`: peak scale deviation (0.18 = ±18%).
    - `frequency`: wobbles per second.

        blob.apply(jelly())
        button.apply(jelly(amplitude=0.3, duration=0.5))
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        src = v2(*input.meta.scale)
        n = max(int(duration * FRAMERATE), 2)
        for i in range(n):
            t = i / (n - 1)
            if i == n - 1:
                yield _scale(src.x, src.y).at(start=start + i * SINGLE_FRAME)
                continue
            wobble = amplitude * math.sin(2 * math.pi * frequency * t * duration) * (1.0 - t)
            yield _scale(src.x * (1 + wobble), src.y * (1 - wobble)).at(start=start + i * SINGLE_FRAME)

    return _apply
