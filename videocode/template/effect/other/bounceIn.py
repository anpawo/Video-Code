#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.opacity import opacity as _opacity
from videocode.shader.vertexShader.position import position as _position
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def bounceIn(
    *,
    height: wnumber = 1.5,
    start: sec = 0,
    duration: sec = 0.8,
) -> Effect:
    """
    Drop the target in from `height` world units above, landing with the
    `Easing.Bounce` ball-bounce. The current position is the landing spot.

        ball.position(0, 0).apply(bounceIn())
        badge.apply(bounceIn(height=2.5, duration=1.0))
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        dst = v2(*input.meta.position)
        src = v2(dst.x, dst.y + height)
        for p, i in Easing.Bounce.rangeIdx(src, dst, duration):
            yield _position(p.x, p.y).at(start=start + i * SINGLE_FRAME)
        for o, i in Easing.Out.rangeIdx(0.0, 255.0, max(duration * 0.3, SINGLE_FRAME * 2)):
            yield _opacity(o).at(start=start + i * SINGLE_FRAME)

    return _apply
