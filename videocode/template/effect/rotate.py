#!/usr/bin/env python3


from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.shader.ishader import DeferredShader, IShader
from videocode.shader.vertexShader.rotate import rotation
from videocode.utils.bezier import *
from videocode.utils.classutils import Maybe


if TYPE_CHECKING:
    from videocode.input.input import Input


class rotateTo(DeferredShader):
    def __init__(
        self,
        dst: unumber,
        *,
        start: sec = 0,
        duration: sec = 0.4,
        easing: easing = Easing.Linear,
    ) -> None:
        self.dst = dst
        self.start = start
        self.duration = duration
        self.easing = easing

    def resolve(self, input: Input) -> Generator[tuple[IShader, sec, sec], Any, None]:
        src = input.meta.rotation

        for o, i in self.easing.rangeIdx(src, self.dst, self.duration):
            yield rotation(o), self.start + i * SINGLE_FRAME, SINGLE_FRAME


class rotateBy(DeferredShader):
    def __init__(
        self,
        dst: unumber,
        *,
        start: sec = 0,
        duration: sec = 0.4,
        easing: easing = Easing.Linear,
    ) -> None:
        self.dst = dst
        self.start = start
        self.duration = duration
        self.easing = easing

    def resolve(self, input: Input) -> Generator[tuple[IShader, sec, sec], Any, None]:
        src = input.meta.rotation
        self.dst += src

        for o, i in self.easing.rangeIdx(src, self.dst, self.duration):
            yield rotation(o), self.start + i * SINGLE_FRAME, SINGLE_FRAME
