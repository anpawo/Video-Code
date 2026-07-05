#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.opacity import opacity as _opacity
from videocode.shader.vertexShader.rotate import rotation as _rotation
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def spinIn(
    *,
    rotations: number = 1.0,
    scale: number = 0.3,
    start: sec = 0,
    duration: sec = 0.7,
    easing: easing = Easing.Out,
) -> Effect:
    """
    Spin the target in: rotates `rotations` full turns while scaling up from
    `scale`x and fading in, decelerating into place.

    On a `Group`/`Text` the effect is dispatched per member, so each member
    spins around its own center (a whirl of letters), not around the group's.

        logo.apply(spinIn())
        title.apply(spinIn(rotations=0.5, duration=0.5))
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        dstRot = input.meta.rotation
        srcRot = dstRot - rotations * 360.0
        dstS = v2(*input.meta.scale)
        srcS = dstS * scale
        for (r, i), (s, _) in zip(easing.rangeIdx(srcRot, dstRot, duration), easing.rangeIdx(srcS, dstS, duration)):
            yield _rotation(r).at(start=start + i * SINGLE_FRAME)
            yield _scale(*s).at(start=start + i * SINGLE_FRAME)
        for o, i in Easing.Out.rangeIdx(0.0, 255.0, max(duration * 0.5, SINGLE_FRAME * 2)):
            yield _opacity(o).at(start=start + i * SINGLE_FRAME)

    return _apply
