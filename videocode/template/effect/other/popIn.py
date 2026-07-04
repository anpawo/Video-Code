#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.opacity import opacity as _opacity
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def popIn(
    *,
    scale: number = 0.5,
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.Back,
) -> Effect:
    """
    Pop the target in: fades in fast while scaling up from `scale`x with an
    overshoot (`Easing.Back` — briefly exceeds the final size, then settles).
    The bouncy entrance every editor ships as "Pop"/"Bounce in".

    - `scale`: starting scale factor relative to the current scale.
    - `easing`: drives the scale; try `Easing.Elastic` for a springier pop.

    The fade runs over the first 40% of `duration` so the shape is fully
    opaque while the overshoot plays out.

        rect.opacity(0).apply(popIn())
        title.apply(popIn(easing=Easing.Elastic, duration=0.8))
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        dst = v2(*input.meta.scale)
        src = dst * scale
        for s, i in easing.rangeIdx(src, dst, duration):
            yield _scale(*s).at(start=start + i * SINGLE_FRAME)
        for o, i in Easing.Out.rangeIdx(0.0, 255.0, max(duration * 0.4, SINGLE_FRAME * 2)):
            yield _opacity(o).at(start=start + i * SINGLE_FRAME)

    return _apply
