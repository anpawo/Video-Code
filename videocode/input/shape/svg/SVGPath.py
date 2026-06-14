#!/usr/bin/env python3


from videocode.input.shape.Polygon import Polygon
from videocode.ty import *


__all__ = [
    "SVGPath",
]


class SVGPath(Polygon):
    """
    A single static shape parsed out of an SVG file — one fixed set of
    anchor-handle contours (outer outline + holes), like `Letter` but for
    arbitrary SVG path/shape data instead of a font glyph.
    """

    def __init__(self, contours: list[list[point]], fillColor: rgba, strokeColor: rgba, strokeWidth: wufloat):
        self._contours = contours
        super().__init__(
            vertices=self.generateVertices(),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
        )

    def generateRawContours(self) -> list[list[point]]:
        return self._contours

    def generateVertices(self) -> list[point]:
        return [p for c in self.generateRawContours() for p in c]
