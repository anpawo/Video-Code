#!/usr/bin/env python3


from videocode.Constant import FR, SF, number
from videocode.transformation.transformation.Position import position
from videocode.utils.bezier import cubicBezier
from videocode.utils.easings import Easing


def moveTo(input, x: number | None = None, y: number | None = None, *, easing: cubicBezier = Easing.Linear, start: number = 0, duration: number = 0.4) -> None:
    n = int((duration - start) * FR)
    srcX = input.meta.position.x
    srcY = input.meta.position.y

    x = x if x else srcX
    y = y if y else srcY

    for i in range(n):
        t = i / (n - 1)
        m = easing(t)

        nx = srcX + (x - srcX) * m
        ny = srcY + (y - srcY) * m

        input.apply(position(nx, ny), start=i * SF)
