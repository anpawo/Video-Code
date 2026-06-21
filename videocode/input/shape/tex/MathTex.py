#!/usr/bin/env python3

from __future__ import annotations

from videocode.constants import TRANSPARENT, WHITE
from videocode.input.interface.Group import Group
from videocode.input.shape.svg._SVGHelper import buildPaths
from videocode.input.shape.svg.SVGPath import SVGPath
from videocode.input.shape.tex._TexHelper import texToSVG
from videocode.ty import *
from videocode.utils.mixins import _hasFillStroke


__all__ = [
    "MathTex",
    "Tex",
]


class MathTex(Group[SVGPath], _hasFillStroke):
    """
    Renders a LaTeX math expression (e.g. `r"\\frac{1}{2} + \\int_0^1 x^2 dx"`)
    as a group of vector shapes — compiled via `latex` + `dvisvgm --no-fonts`
    (`_TexHelper.texToSVG`) and loaded through the same SVG pipeline as `SVG`
    (`_SVGHelper.buildPaths`).

    Unlike `SVG`, every shape is recolored to `fillColor`/`strokeColor`/
    `strokeWidth` (dvisvgm always renders solid black) — via `_hasFillStroke`,
    so `formula.fillColor = RED_A` recolors the whole formula afterwards.

    `width`/`height` (world units) scale the whole formula; independently when
    both are given, uniformly (preserving aspect ratio) when only one is
    given, or at natural size (scaled by `WORLD_TO_SCREEN_RATIO`) when
    neither is given.
    """

    def __init__(
        self,
        tex: str,
        fillColor: rgba = WHITE,
        strokeColor: rgba = TRANSPARENT,
        strokeWidth: wufloat = 0,
        width: maybe[wunumber] = None,
        height: maybe[wunumber] = None,
        mathMode: bool = True,
    ):
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth

        svgPath = texToSVG(tex, mathMode=mathMode)
        super().__init__(*buildPaths(svgPath, width, height, fillColor, strokeColor, strokeWidth))


class Tex(MathTex):
    """
    Like `MathTex`, but `tex` is inserted verbatim as the document body
    instead of being wrapped in `$...$` — use for plain text or LaTeX
    constructs (e.g. `align*`) that shouldn't be in math mode.
    """

    def __init__(
        self,
        tex: str,
        fillColor: rgba = WHITE,
        strokeColor: rgba = TRANSPARENT,
        strokeWidth: wufloat = 0,
        width: maybe[wunumber] = None,
        height: maybe[wunumber] = None,
    ):
        super().__init__(tex, fillColor, strokeColor, strokeWidth, width, height, mathMode=False)
