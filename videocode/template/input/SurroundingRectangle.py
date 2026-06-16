#!/usr/bin/env python3

from __future__ import annotations

from videocode import *


class SurroundingRectangle(Rectangle):
    """
    A Rectangle outline drawn around `shape`'s bounding box (its local
    `vertices`, expanded by `buff` on every side) — Manim's
    `SurroundingRectangle`, useful for highlighting an element.

    Like `Shadow`, independent of `shape` after creation: position, scale,
    rotation and zIndex are copied once at creation time — create after
    `shape`'s final transform.
    """

    def __init__(
        self,
        shape: Polygon,
        buff: wnumber = 0.25,
        color: rgba = YELLOW,
        strokeWidth: wufloat = 0.05,
        cornerRadius: percent = 0,
    ):
        xs = [v[0] for v in shape.vertices]
        ys = [v[1] for v in shape.vertices]
        width = (max(xs) - min(xs)) + 2 * buff
        height = (max(ys) - min(ys)) + 2 * buff

        super().__init__(
            width=width,
            height=height,
            fillColor=TRANSPARENT,
            strokeColor=color,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )
        self.position(shape.meta.position.x, shape.meta.position.y)
        self.scale(x=shape.meta.scale.x, y=shape.meta.scale.y)
        self.rotation(shape.meta.rotation)
        self.zIndex(shape.meta.zIndex + 1)
