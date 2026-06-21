#!/usr/bin/env python3

from __future__ import annotations

from videocode.input.interface.Group import Group
from videocode.input.shape.svg._SVGHelper import buildPaths
from videocode.input.shape.svg.SVGPath import SVGPath
from videocode.ty import *


__all__ = [
    "SVG",
]


class SVG(Group[SVGPath]):
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
        super().__init__(*buildPaths(filepath, width, height))
