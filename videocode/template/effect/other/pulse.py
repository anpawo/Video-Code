#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def pulse(
    *,
    scale: number = 1.15,
    times: int = 1,
    start: sec = 0,
    duration: sec = 0.6,
    easing: easing = Easing.ThereAndBack,
) -> Effect:
    """
    Heartbeat emphasis: scale up to `scale`x and back, `times` times over
    `duration`. Like `highlight()` without the color flash.

        icon.apply(pulse())
        icon.apply(pulse(times=2, scale=1.25))
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        src = v2(*input.meta.scale)
        dst = src * scale
        per = duration / times
        for r in range(times):
            for s, i in easing.rangeIdx(src, dst, per):
                yield _scale(*s).at(start=start + r * per + i * SINGLE_FRAME)

    return _apply
