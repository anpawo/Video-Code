#!/usr/bin/env python3

from __future__ import annotations

import math

from videocode import *


class Underline(HorizontalLine):
    """
    A rounded `HorizontalLine` drawn under `shape`'s bounding box (its local
    `vertices`), offset by `buff` below the bottom edge — Manim's
    `Underline`, useful for emphasizing a word or expression.

    Like `Shadow`/`SurroundingRectangle`, independent of `shape` after
    creation: position, scale, rotation and zIndex are copied once at
    creation time — create after `shape`'s final transform.
    """

    def __init__(
        self,
        shape: Polygon,
        buff: wnumber = 0.1,
        color: rgba = WHITE,
        strokeWidth: wufloat = 0.05,
    ):
        xs = [v[0] for v in shape.vertices]
        ys = [v[1] for v in shape.vertices]
        length = (max(xs) - min(xs)) + 2 * buff
        shapeHeight = max(ys) - min(ys)

        super().__init__(
            length=length,
            strokeWidth=strokeWidth,
            fillColor=color,
            strokeColor=TRANSPARENT,
            rounded=True,
        )

        sx, sy = shape.meta.scale
        localOffsetY = -(shapeHeight / 2 * sy + buff + strokeWidth / 2)
        rad = math.radians(shape.meta.rotation)
        dx = -localOffsetY * math.sin(rad)
        dy = localOffsetY * math.cos(rad)

        self.position(shape.meta.position.x + dx, shape.meta.position.y + dy)
        self.scale(x=sx, y=sy)
        self.rotation(shape.meta.rotation)
        self.zIndex(shape.meta.zIndex + 1)
