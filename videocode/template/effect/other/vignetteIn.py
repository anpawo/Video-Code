#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from videocode.constants import *
from videocode.shader.fragmentShader.vignette import vignette as _vignette
from videocode.shader.ishader import Effect, IShader
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def vignetteIn(
    *,
    intensity: number = 0.55,
    radius: percent = 42,
    smoothness: percent = 60,
    start: sec = 0,
    duration: sec = 1.2,
    easing: easing = Easing.Out,
) -> Effect:
    """
    Close the corners in progressively instead of switching a vignette on.
    Used under a zoom it reads as the frame tightening with the camera.

    The vignette PERSISTS at full `intensity` after `duration` — it is a look,
    not a beat. Reverse it with `vignetteIn(intensity=0)` later, or wrap the
    whole thing in `vignetteBeat`.

        clip.apply(vignetteIn())
        clip.apply(vignetteIn(intensity=0.8, radius=30, duration=2))
    """

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        for v, i in easing.rangeIdx(0.0, float(intensity), duration):
            yield _vignette(v, radius, smoothness).at(start=start + i * SINGLE_FRAME)

    return _apply


def vignetteBeat(
    *,
    intensity: number = 0.6,
    radius: percent = 42,
    smoothness: percent = 60,
    start: sec = 0,
    duration: sec = 1.6,
) -> Effect:
    """
    `vignetteIn` that opens back up — the corners breathe in and out once
    over `duration`, leaving the image untouched afterwards.

        clip.apply(vignetteBeat(duration=2))
    """

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        for v, i in Easing.ThereAndBack.rangeIdx(0.0, float(intensity), duration):
            yield _vignette(v, radius, smoothness).at(start=start + i * SINGLE_FRAME)

    return _apply
