#!/usr/bin/env python3


from videocode.Constant import FR, SR, number
from videocode.Decorators import noAutoAdd
from videocode.transformation.setter.SetPosition import setPosition
from videocode.utils.bezier import cubicBezier
from videocode.utils.easings import Easing


@noAutoAdd
def slideTo(input, x: number, y: number, *, easing: cubicBezier = Easing.Linear, start: number = 0, duration: number = 0.4) -> None:
    n = int((duration - start) * FR) + 1
    srcX = input.meta.x
    srcY = input.meta.y

    for i in range(n):
        t = i / (n - 1)
        m = easing(t)

        nx = srcX + (x - srcX) * m
        ny = srcY + (y - srcY) * m

        input.apply(setPosition(nx, ny), start=i * SR)
