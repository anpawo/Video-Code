#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.position import position as _position
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def kenBurns(
    *,
    zoom: number = 1.15,
    panX: wnumber = 0.15,
    panY: wnumber = 0.0,
    start: sec = 0,
    duration: sec = 4.0,
    easing: easing = Easing.Linear,
) -> Effect:
    """
    Ken Burns motion for stills: a slow simultaneous zoom to `zoom`x and pan
    by (`panX`, `panY`) world units over `duration`. The default treatment
    every editor applies to photos.

    Use a negative `zoom` delta by passing `zoom < 1` to zoom out instead.

        img = Image("photo.png").position(0, 0)
        img.apply(kenBurns())
        img.apply(kenBurns(zoom=1.25, panX=-0.2, panY=0.1, duration=6))
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        srcS = v2(*input.meta.scale)
        dstS = srcS * zoom
        srcP = v2(*input.meta.position)
        dstP = v2(srcP.x + panX, srcP.y + panY)
        for (s, i), (p, _) in zip(easing.rangeIdx(srcS, dstS, duration), easing.rangeIdx(srcP, dstP, duration)):
            yield _scale(*s).at(start=start + i * SINGLE_FRAME)
            yield _position(p.x, p.y).at(start=start + i * SINGLE_FRAME)

    return _apply
