#!/usr/bin/env python3

from __future__ import annotations

import math

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.opacity import opacity as _opacity
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def stamp(
    *,
    scale: number = 2.5,
    start: sec = 0,
    duration: sec = 0.6,
) -> Effect:
    """
    Slam the target down like a rubber stamp: starts huge and transparent,
    crashes to full size fast (accelerating), then a brief impact wobble.
    The meme-caption / "APPROVED" entrance.

    - `scale`: starting size multiplier.

        Text("APPROVED", fillColor=RED).apply(stamp())
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        dst = v2(*input.meta.scale)
        src = dst * scale
        slam = max(duration * 0.35, SINGLE_FRAME * 2)
        wobbleDur = max(duration - slam, SINGLE_FRAME * 2)

        for s, i in Easing.In.rangeIdx(src, dst, slam):
            yield _scale(*s).at(start=start + i * SINGLE_FRAME)
        for o, i in Easing.In.rangeIdx(0.0, 255.0, slam):
            yield _opacity(o).at(start=start + i * SINGLE_FRAME)

        # Impact wobble: small decaying overshoot ripple after the slam.
        n = max(int(wobbleDur * FRAMERATE), 2)
        for i in range(n):
            t = i / (n - 1)
            if i == n - 1:
                yield _scale(dst.x, dst.y).at(start=start + slam + i * SINGLE_FRAME)
                continue
            ripple = 0.06 * math.sin(2 * math.pi * 3 * t) * (1.0 - t)
            yield _scale(dst.x * (1 + ripple), dst.y * (1 + ripple)).at(start=start + slam + i * SINGLE_FRAME)

    return _apply
