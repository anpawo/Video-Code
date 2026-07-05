#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.rotate import rotation as _rotation
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input

# Animate.css "tada" keyframes: (t, scale, rotation°). Shrink + tilt back,
# then celebrate — enlarged wobble left/right — and settle.
_KEYS: list[tuple[float, float, float]] = [
    (0.0, 1.0, 0.0),
    (0.1, 0.9, -3.0),
    (0.2, 0.9, -3.0),
    (0.3, 1.1, 3.0),
    (0.4, 1.1, -3.0),
    (0.5, 1.1, 3.0),
    (0.6, 1.1, -3.0),
    (0.7, 1.1, 3.0),
    (0.8, 1.1, -3.0),
    (0.9, 1.1, 3.0),
    (1.0, 1.0, 0.0),
]


def tada(
    *,
    start: sec = 0,
    duration: sec = 1.0,
) -> Effect:
    """
    The celebration wobble (Animate.css "tada"): shrink + tilt, then an
    enlarged left-right shimmy, settling back to normal. The go-to
    "achievement unlocked" emphasis.

        badge.apply(tada())
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        srcS = v2(*input.meta.scale)
        srcR = input.meta.rotation
        n = max(int(duration * FRAMERATE), 2)
        for i in range(n):
            t = i / (n - 1)
            # Linear interpolation between the surrounding keyframes.
            s, r = 1.0, 0.0
            for (t0, s0, r0), (t1, s1, r1) in zip(_KEYS, _KEYS[1:]):
                if t0 <= t <= t1:
                    m = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
                    s = s0 + (s1 - s0) * m
                    r = r0 + (r1 - r0) * m
                    break
            yield _scale(srcS.x * s, srcS.y * s).at(start=start + i * SINGLE_FRAME)
            yield _rotation(srcR + r).at(start=start + i * SINGLE_FRAME)

    return _apply
