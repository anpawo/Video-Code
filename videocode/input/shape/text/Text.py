#!/usr/bin/env python3


from videocode.input.interface.Interface import Interface
from videocode.input.interface.Offset import Offset
import videocode.input.shape.text._TextHelper as _helper


from videocode.input.shape.Polygon import Polygon
from videocode.input.interface.Group import Group
from videocode.input.shape.text.Letter import Letter
from videocode.shader.vertexShader.hide import hide
from videocode.utils.decorators import prop, propagate
from videocode.ty import *
from videocode.constants import *
from videocode.utils.mixins import _hasFillStroke


__all__ = [
    "Letter",
    "Text",
]


class Text(Group[Offset[Letter]], _hasFillStroke):
    def __init__(
        self,
        text: str,
        fontSize: wnumber = 0.5,
        fontFamily: str = "Inter",
        fillColor: rgba = WHITE,
        strokeColor: rgba = TRANSPARENT,
        strokeWidth: wufloat = 0,
        bold: bool = False,
        italic: bool = False,
    ):
        # Method vs Property: why ?
        self.text = text
        self.fontSize = fontSize
        self.fontFamily = fontFamily
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth
        self.bold = bold
        self.italic = italic

        super().__init__(
            *(
                _helper.buildLetters(
                    text=text,
                    fontSize=fontSize,
                    fontFamily=fontFamily,
                    bold=bold,
                    italic=italic,
                    fillColor=fillColor,
                    strokeColor=strokeColor,
                    strokeWidth=strokeWidth,
                )
                if len(text) != 0
                else []
            )
        )
        self.alignLetters()

    @prop()
    def text() -> str: ...

    @text.setter
    def textSetter(self, value: str) -> None:
        # hide exceedent or show hidden letters
        l = len(self.inputs)  # actual current letters, not self.text (already updated)
        r = len(value)
        if l > r:
            for i in range(l - r):
                self.inputs[-i - 1].hide()
        elif l < r:
            for i in range(r - l):
                self.inputs.append(Offset(Letter(value[l + i], *self.config())))

        for i in range(min(l, r)):
            self.inputs[i].show()
            self.inputs[i].input.char = value[i]

        self.alignLetters()

    def config(self) -> tuple[wnumber, str, rgba, rgba, wnumber, bool, bool]:
        return (
            self.fontSize,
            self.fontFamily,
            self.fillColor,
            self.strokeColor,
            self.strokeWidth,
            self.bold,
            self.italic,
        )

    def alignLetters(self) -> None:
        n = len(self.text)
        letters = self.inputs[:n]
        if not letters:
            return

        data = _helper.buildLetterData(
            text=self.text,
            fontSize=self.fontSize,
            fontFamily=self.fontFamily,
            bold=self.bold,
            italic=self.italic,
        )
        if not data:
            return

        x_min = min(x for _, x, _ in data)
        x_max = max(x + l.input.width for (_, x, _), l in zip(data, letters))
        ax = x_min + self.meta.align.x * (x_max - x_min)
        ay = _helper.lineAnchor(self.fontFamily, self.bold, self.italic, self.fontSize, self.meta.align.y)

        for l, (_, x, y) in zip(letters, data):
            l.align(x=0, y=0)
            l.xOffset = x - ax
            l.yOffset = y - ay

    @propagate
    def fontSize() -> wnumber: ...
    @propagate
    def fontFamily() -> str: ...
    @propagate
    def bold() -> bool: ...
    @propagate
    def italic() -> bool: ...

    @property
    def width(self) -> wunumber:
        return sum(l.input.width for l in self.inputs) if self.inputs else 0

    @property
    def height(self) -> wunumber:
        return max(l.input.height for l in self.inputs) if self.inputs else 0

    def __str__(self) -> str:
        return f"Text({self.text})"

    # fontFamily / size ...
