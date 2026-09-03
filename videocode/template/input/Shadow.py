#!/usr/bin/env python3

from __future__ import annotations

from videocode import *


class Shadow(Polygon):
    """
    A copy of `shape`'s geometry, filled with a single `color`, offset by
    `offset`, and rendered behind `shape` via `zIndex`.

    Just a `Polygon` — independent of `shape` after creation: position, scale,
    rotation and zIndex are copied once. Move/scale/etc. `shape` first, then
    create the `Shadow`.
    """

    def __init__(
        self,
        shape: Polygon,
        offset: tuple[wnumber, wnumber] = (0.25, -0.25),
        color: rgba = BLACK | 0.5,
        blurStrength: unumber = 4,
    ):
        super().__init__(
            vertices=list(shape.vertices),
            fillColor=color,
            strokeColor=TRANSPARENT,
            strokeWidth=0,
            cornerRadius=shape.cornerRadius,
            sharpCorners=shape.sharpCorners,
        )
        ox, oy = offset
        # `offset` stays in world units on purpose: a drop shadow's offset is
        # the light direction, so it must not turn or grow with the shape.
        self.position(shape.meta.position.x + ox, shape.meta.position.y + oy)
        self.scale(x=shape.meta.scale.x, y=shape.meta.scale.y)
        self.rotation(shape.meta.rotation)
        self.apply(zIndex(shape.meta.zIndex - 1))
        self.apply(blur(blurStrength))

    def generateVertices(self) -> list[point]:
        return self.vertices
