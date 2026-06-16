#!/usr/bin/env python3

from __future__ import annotations

import math

from videocode import *


class Cross(Group[HorizontalLine]):
    """
    An "X" made of two diagonal `HorizontalLine`s spanning `shape`'s
    bounding box (its local `vertices`), expanded by `buff` on every side —
    Manim's `Cross`, useful for marking something as wrong/removed.

    Like `Shadow`/`SurroundingRectangle`/`Underline`, independent of `shape`
    after creation: position, scale, rotation and zIndex are copied once at
    creation time — create after `shape`'s final transform.
    """

    def __init__(
        self,
        shape: Polygon,
        buff: wnumber = 0.1,
        color: rgba = RED,
        strokeWidth: wufloat = 0.05,
    ):
        xs = [v[0] for v in shape.vertices]
        ys = [v[1] for v in shape.vertices]
        width = (max(xs) - min(xs)) + 2 * buff
        height = (max(ys) - min(ys)) + 2 * buff

        length = math.hypot(width, height)
        angle = math.degrees(math.atan2(height, width))
        rotation = shape.meta.rotation

        def diagonal(degree: number) -> HorizontalLine:
            return HorizontalLine(
                length=length,
                strokeWidth=strokeWidth,
                fillColor=color,
                strokeColor=TRANSPARENT,
                rounded=True,
            ).rotation(degree + rotation)

        super().__init__(diagonal(angle), diagonal(-angle))

        sx, sy = shape.meta.scale
        self.position(shape.meta.position.x, shape.meta.position.y)
        self.scale(x=sx, y=sy)
        self.zIndex(shape.meta.zIndex + 1)
