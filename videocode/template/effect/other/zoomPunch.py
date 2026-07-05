#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def zoomPunch(
    *,
    scale: number = 1.35,
    start: sec = 0,
    duration: sec = 0.5,
) -> Effect:
    """
    Zoom punch: snaps up to `scale`x almost instantly, then settles back to
    the original size with a Back-easing overshoot (dips slightly below 1
    before landing). The beat-drop / impact emphasis every editor has.

        thumbnail.apply(zoomPunch())
        beat.apply(zoomPunch(scale=1.6, duration=0.4))
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        src = v2(*input.meta.scale)
        peak = src * scale
        up = max(duration * 0.25, SINGLE_FRAME * 2)
        down = max(duration - up, SINGLE_FRAME * 2)
        for s, i in Easing.Out.rangeIdx(src, peak, up):
            yield _scale(*s).at(start=start + i * SINGLE_FRAME)
        for s, i in Easing.Back.rangeIdx(peak, src, down):
            yield _scale(*s).at(start=start + up + i * SINGLE_FRAME)

    return _apply
