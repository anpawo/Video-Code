#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.shader.vertexShader.args import args
from videocode.utils.bezier import *


def highlight(
    *,
    scale: number = 1.2,
    color: maybe[rgba] = YELLOW,
    start: sec = 0,
    duration: sec = 1.0,
    easing: easing = Easing.ThereAndBack,
) -> Effect:
    """
    Briefly scales the target up by `scaleFactor` and flashes its `fillColor`
    toward `color`, both returning to their original values via
    `Easing.ThereAndBack`.

    Returns an `Effect` callable. Pass to `apply`:
        g.apply(highlight())
        g.apply(highlight(color=RED, scaleFactor=1.5))
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        srcScale = v2(*input.meta.scale)
        dstScale = srcScale * scale
        for s, i in easing.rangeIdx(srcScale, dstScale, duration):
            yield _scale(*s).at(start=start + i * SINGLE_FRAME)
        srcColor = getattr(input, "fillColor", None)
        if color is not None and srcColor is not None:
            for c, i in easing.rangeIdx(srcColor, color, duration):
                yield args("fillColor", c).at(start=start + i * SINGLE_FRAME)

    return _apply
