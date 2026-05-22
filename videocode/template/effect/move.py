#!/usr/bin/env python3


from typing import TYPE_CHECKING, Generator, Protocol
from videocode.constants import *
from videocode.shader.ishader import DeferredShader, IShader
from videocode.utils.bezier import *
from videocode.shader.vertexShader.position import position
from videocode.utils.classutils import Maybe


if TYPE_CHECKING:
    from videocode.input.input import Input


class moveTo(DeferredShader):
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
        src = v2(*input.meta.position)
        dst = v2(
            Maybe(self.x) | src.x,
            Maybe(self.y) | src.y,
        )

        for p, i in self.easing.rangeIdx(src, dst, self.duration):
            yield position(*p), self.start + i * SINGLE_FRAME, SINGLE_FRAME


class moveBy(DeferredShader):
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
        src = v2(*input.meta.position)
        dst = v2(
            src.x + (Maybe(self.x) | 0),
            src.y + (Maybe(self.y) | 0),
        )

        for p, i in self.easing.rangeIdx(src, dst, self.duration):
            yield position(*p), self.start + i * SINGLE_FRAME, SINGLE_FRAME
