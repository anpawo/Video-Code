#!/usr/bin/env python3

from __future__ import annotations

from videocode import *


class Shadow(Polygon):
    """
    A copy of `shape`'s geometry, filled with a single `color`, offset by
    `offset`, and rendered behind `shape` via `zIndex`.

    Just a `Polygon` — independent of `shape` after creation. Move/scale/etc.
    `shape` first, then create the `Shadow`.
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
        self.position(shape.meta.position.x + ox, shape.meta.position.y + oy)
        self.apply(zIndex(shape.meta.zIndex - 1))
        self.apply(blur(blurStrength))

    def generateVertices(self) -> list[point]:
        return self.vertices
