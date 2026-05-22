#!/usr/bin/env python3


from typing import TYPE_CHECKING

from videocode.constants import *
from videocode.shader.ishader import DeferredShader, IShader
from videocode.shader.vertexShader.opacity import opacity
from videocode.utils.bezier import *
from videocode.utils.classutils import Maybe

if TYPE_CHECKING:
    from videocode.input.input import Input


class fadeTo(DeferredShader):
    def __init__(
        self,
        src: maybe[unumber],
        dst: unumber,
        *,
        start: sec = 0,
        duration: sec = 0.4,
        easing: easing = Easing.Linear,
    ) -> None:
        self.src = src
        self.dst = dst
        self.start = start
        self.duration = duration
        self.easing = easing

    def resolve(self, input: Input) -> Generator[tuple[IShader, sec, sec], Any, None]:
        self.src = Maybe(self.src) | input.meta.opacity

        for o, i in self.easing.rangeIdx(self.src, self.dst, self.duration):
            yield opacity(o), self.start + i * SINGLE_FRAME, SINGLE_FRAME
