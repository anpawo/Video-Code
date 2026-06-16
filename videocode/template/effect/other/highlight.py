#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader
from videocode.shader.vertexShader.scale import scale
from videocode.shader.vertexShader.args import args
from videocode.utils.bezier import *


if TYPE_CHECKING:
    from videocode.input.shape.Polygon import Polygon


def highlight(
    input: "Polygon",
    *,
    scaleFactor: number = 1.2,
    color: maybe[rgba] = YELLOW,
    start: sec = 0,
    duration: sec = 1.0,
    easing: easing = Easing.ThereAndBack,
) -> Generator[IShader, Any, None]:
    """
    Briefly scales `input` up by `scaleFactor` and flashes its `fillColor`
    toward `color`, both returning to their original values via
    `Easing.ThereAndBack` (`self(0) == self(1) == 0`).
    """
    srcScale = v2(*input.meta.scale)
    dstScale = srcScale * scaleFactor
    for s, i in easing.rangeIdx(srcScale, dstScale, duration):
        yield scale(*s).at(start=start + i * SINGLE_FRAME)

    if color is not None:
        srcColor: rgba = input.fillColor
        for c, i in easing.rangeIdx(srcColor, color, duration):
            yield args("fillColor", c).at(start=start + i * SINGLE_FRAME)
