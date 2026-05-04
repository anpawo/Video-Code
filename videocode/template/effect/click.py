#!/usr/bin/env python3


from videocode.ty import *
from videocode.constants import FRAMERATE, SINGLE_FRAME
from videocode.shader.vertexShader.scale import scale
from videocode.utils.bezier import Easing


def click(
    low=0.85,
    up=1.0,
    start: sec = 0,
    duration: sec = 0.4,
    easing=Easing.InOut,
):

    half = duration / 2
    n = int(half * FRAMERATE)

    def generator():
        for s, i in easing.rangeIdx(up, low, half):
            yield scale(s, s), start + i * SINGLE_FRAME, SINGLE_FRAME
        for s, i in easing.rangeIdx(low, up, half):
            yield scale(s, s), start + (i + n) * SINGLE_FRAME, SINGLE_FRAME

    return generator()
