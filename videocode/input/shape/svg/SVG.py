#!/usr/bin/env python3


from videocode.input.interface.Group import Group
from videocode.input.interface.Offset import Offset
from videocode.input.shape.svg._SVGHelper import parseSVG
from videocode.input.shape.svg.SVGPath import SVGPath
from videocode.ty import *


__all__ = [
    "SVG",
]


class SVG(Group[Offset[SVGPath]]):
    """
    Renders an SVG file as a group of static `SVGPath` shapes, one per
    top-level shape element (rect/circle/path/...), positioned relative to
    each other as in the source file.

    `width`/`height` (world units) scale the whole SVG; independently when
    both are given, uniformly (preserving aspect ratio) when only one is
    given, or at natural size (scaled by `WORLD_TO_SCREEN_RATIO`) when
    neither is given.
    """

    def __init__(self, filepath: str, width: maybe[wunumber] = None, height: maybe[wunumber] = None):
        offsets: list[Offset[SVGPath]] = []
        for contours, fillColor, strokeColor, strokeWidth in parseSVG(filepath, width, height):
            pts = [p for c in contours for p in c]
            minX = min(p[0] for p in pts)
            minY = min(p[1] for p in pts)
            path = SVGPath(contours, fillColor, strokeColor, strokeWidth)
            offsets.append(Offset(path, x=minX, y=minY))

        super().__init__(*offsets)
