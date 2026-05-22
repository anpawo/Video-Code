#!/usr/bin/env python3


from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.shader.ishader import DeferredShader, IShader
from videocode.shader.vertexShader.align import align
from videocode.utils.bezier import *
from videocode.utils.classutils import Maybe


if TYPE_CHECKING:
    from videocode.input.input import Input


class alignTo(DeferredShader):
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
        self.easing = easing
        self.start = start
        self.duration = duration

    def resolve(self, input: Input) -> Generator[tuple[IShader, sec, sec], Any, None]:
        src = v2(*input.meta.position)
        dst = v2(
            Maybe(self.x) | src.x,
            Maybe(self.y) | src.y,
        )

        for a, i in self.easing.rangeIdx(src, dst, self.duration):
            yield align(*a), self.start + i * SINGLE_FRAME, SINGLE_FRAME
