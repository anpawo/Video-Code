#!/usr/bin/env python3


from videocode.Constant import FR, SR, position
from videocode.Global import Global
from videocode.input.Input import Input
from videocode.transformation.Transformation import Transformation
from videocode.transformation.setter.SetPosition import setPosition
from videocode.utils.bezier import cubicBezier
from videocode.utils.easings import Easing


def slideTo(input: Input, x: position, y: position, *, easing: cubicBezier = Easing.Linear, start=0, duration=0.3) -> None:
    n = int((duration - start) * FR) + 1
    srcX = input.meta.x
    srcY = input.meta.y

    previousState = Global.automaticAdder
    Global.automaticAdder = False

    for i in range(n):
        t = i / (n - 1)
        m = easing(t)

        nx = srcX + (x - srcX) * m
        ny = srcY + (y - srcY) * m

        input.apply(setPosition(nx, ny), start=i * SR)

    Global.automaticAdder = previousState
