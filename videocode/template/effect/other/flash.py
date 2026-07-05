#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.fragmentShader.brightness import brightness as _brightness
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def flash(
    *,
    amount: number = 160,
    times: int = 1,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.ThereAndBack,
) -> Effect:
    """
    Flash the target bright and back, `times` times — the white-blink
    emphasis (works on images and video too, unlike a fillColor flash).

    - `amount`: peak brightness offset (0-255); negative values give a
      dark-blink instead.

        icon.apply(flash())
        frame.apply(flash(times=3, duration=0.9))
    """

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        per = duration / times
        for r in range(times):
            for b, i in easing.rangeIdx(0.0, float(amount), per):
                if abs(b) >= 1.0:
                    yield _brightness(int(b)).at(start=start + r * per + i * SINGLE_FRAME)

    return _apply
