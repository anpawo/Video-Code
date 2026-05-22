#!/usr/bin/env python3


from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.shader.ishader import DeferredShader, IShader
from videocode.shader.vertexShader.scale import scale
from videocode.utils.bezier import *
from videocode.utils.classutils import Maybe


if TYPE_CHECKING:
    from videocode.input.input import Input


class scaleTo(DeferredShader):
    def __init__(
        self,
        x: maybe[wnumber] = None,
        y: maybe[wnumber] = None,
        *,
        start: sec = 0,
        duration: sec = 0.4,
        easing: easing = Easing.Linear,
    ) -> None:
        self.x = x
        self.y = y
        self.start = start
        self.duration = duration
        self.easing = easing

    def resolve(self, input: Input) -> Generator[tuple[IShader, sec, sec], Any, None]:
        src = v2(*input.meta.scale)
        dst = v2(
            Maybe(self.x) | src.x,
            Maybe(self.y) | src.y,
        )

        for s, i in self.easing.rangeIdx(src, dst, self.duration):
            yield scale(*s), self.start + i * SINGLE_FRAME, SINGLE_FRAME


class scaleBy(DeferredShader):
    def __init__(
        self,
        x: maybe[wnumber] = None,
        y: maybe[wnumber] = None,
        *,
        start: sec = 0,
        duration: sec = 0.4,
        easing: easing = Easing.Linear,
    ) -> None:
        self.x = x
        self.y = y
        self.start = start
        self.duration = duration
        self.easing = easing

    def resolve(self, input: Input) -> Generator[tuple[IShader, sec, sec], Any, None]:
        src = v2(*input.meta.scale)
        dst = v2(
            Maybe(self.x) | 0 + src.x,
            Maybe(self.y) | 0 + src.y,
        )

        for s, i in self.easing.rangeIdx(src, dst, self.duration):
            yield scale(*s), self.start + i * SINGLE_FRAME, SINGLE_FRAME
