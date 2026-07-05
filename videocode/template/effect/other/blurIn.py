#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.fragmentShader.blur import blur as _blur
from videocode.shader.vertexShader.opacity import opacity as _opacity
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def blurIn(
    *,
    strength: unumber = 21,
    start: sec = 0,
    duration: sec = 0.6,
    easing: easing = Easing.Out,
) -> Effect:
    """
    Defocus reveal: fades in while a per-frame `blur` resolves from
    `strength` down to sharp.

    Blur strengths must be odd — the eased value is snapped to the nearest
    odd integer per frame (even kernels have no center texel).

        photo.apply(blurIn())
        title.apply(blurIn(strength=31, duration=1.0))
    """

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        n = max(int(duration * FRAMERATE), 2)
        for i in range(n):
            t = i / (n - 1)
            raw = strength * (1.0 - easing(t))
            odd = max(int(raw) | 1, 1)  # snap to odd; 1 ≈ passthrough
            if odd > 1:
                yield _blur(odd).at(start=start + i * SINGLE_FRAME)
        for o, i in Easing.Out.rangeIdx(0.0, 255.0, max(duration * 0.5, SINGLE_FRAME * 2)):
            yield _opacity(o).at(start=start + i * SINGLE_FRAME)

    return _apply
