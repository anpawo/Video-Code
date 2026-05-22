#!/usr/bin/env python3


import videocode.input.shape.text._TextHelper as _helper


from videocode.input.shape.Polygon import Polygon
from videocode.utils.decorators import prop
from videocode.ty import *
from videocode.constants import *


__all__ = [
    "Letter",
]


class Letter(Polygon):
    def __init__(
        self,
        char: str,
        fontSize: wnumber,
        fontFamily: str,
        fillColor: rgba = WHITE,
        strokeColor: rgba = TRANSPARENT,
        strokeWidth: wufloat = 0,
        bold: bool = False,
        italic: bool = False,
    ):
        self.char = char
        self.fontSize = fontSize
        self.fontFamily = fontFamily
        self.bold = bold
        self.italic = italic

        super().__init__(
            vertices=self.generateVertices(),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
        )

    def generateVertices(self) -> list[point]:
        path = _helper.fontPath(self.fontFamily, self.bold, self.italic)
        ft, _, _, capH, _ = _helper.loadFaces(path)
        glyph = ft.get_char_index(ord(self.char)) if self.char else 0
        scale = self.fontSize / capH if capH else 0
        return [(x * scale, y * scale) for x, y in _helper._glyphVerts(path, glyph)]

    @prop(onSet=Polygon.updatePoints)
    def char() -> str: ...

    @prop(onSet=Polygon.updatePoints)
    def fontSize() -> wnumber: ...

    @prop(onSet=Polygon.updatePoints)
    def fontFamily() -> str: ...

    @prop(onSet=Polygon.updatePoints)
    def bold() -> bool: ...

    @prop(onSet=Polygon.updatePoints)
    def italic() -> bool: ...

    def __str__(self) -> str:
        return f"Letter({self.char})"
