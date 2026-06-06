#!/usr/bin/env python3


from typing import Generator

from videocode.ty import *
from videocode.constants import FRAMERATE, SINGLE_FRAME
from videocode.shader.vertexShader.scale import scale
from videocode.utils.bezier import Easing


class click:
    def __init__(
        self,
        low: number = 0.85,
        up: number = 1.0,
        *,
        start: sec = 0,
        duration: sec = 0.2,
        easing=Easing.InOut,
    ) -> None:
        self.low = low
        self.up = up
        self.start = start
        self.duration = duration
        self.easing = easing

    def __iter__(self) -> Generator[scale, Any, None]:
        half = self.duration / 2
        n = int(half * FRAMERATE)

        for s, i in self.easing.rangeIdx(self.up, self.low, half):
            yield scale(s, s).at(start=self.start + i * SINGLE_FRAME)
        for s, i in self.easing.rangeIdx(self.low, self.up, half):
            yield scale(s, s).at(start=self.start + (i + n) * SINGLE_FRAME)
