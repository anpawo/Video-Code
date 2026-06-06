#!/usr/bin/env python3


from copy import copy as _shallow_copy
from videocode.input.interface.Interface import Interface
from videocode.input.interface.Offset import Offset
import videocode.input.shape.text._TextHelper as _helper


from videocode.input.shape.Polygon import Polygon
from videocode.input.interface.Group import Group
from videocode.input.shape.text.Letter import Letter
from videocode.shader.vertexShader.align import align
from videocode.shader.vertexShader.hide import hide
from videocode.utils.classutils import At
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
        l = len(self.inputs)
        r = len(value)
        if l > r:
            for i in range(l - r):
                self.inputs[-i - 1].hide()
        elif l < r:
            target = self.inputs[0].input.meta.transformationOffset if self.inputs else 0
            for i in range(r - l):
                newLetter = Offset(Letter(value[l + i], *self.config()))
                if target > newLetter.input.meta.transformationOffset:
                    newLetter.hide()
                    newLetter.input.waitTo(target)
                    newLetter.show()
                self.inputs.append(newLetter)

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

    def apply(self, *shaders, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        for s in shaders:
            if isinstance(s, align):
                _s, _d, _o = s.resolve(start, duration, offset)
                _shallow_copy(s).modify(self)
                self.alignLetters(start=_s, duration=_d, offset=_o)
            else:
                super().apply(s, start=start, duration=duration, offset=offset)
        return self

    def alignLetters(self, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> None:
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

        x_min = min(x for _, x, _ in data)
        x_max = max(x + l.input.width for (_, x, _), l in zip(data, letters))
        ax = x_min + self.meta.align.x * (x_max - x_min)

        ay = _helper.lineAnchor(self.fontFamily, self.bold, self.italic, self.fontSize, self.meta.align.y)

        for l, (_, x, y) in zip(letters, data):
            l.align(x=0, y=0)  # gets canceled out after first iteration
            l.xOffset = (x - ax) @ At(start, duration, offset)
            l.yOffset = (y - ay) @ At(start, duration, offset)

    @propagate(after=alignLetters)
    def fontSize() -> wnumber: ...
    @propagate(after=alignLetters)
    def fontFamily() -> str: ...
    @propagate(after=alignLetters)
    def bold() -> bool: ...
    @propagate(after=alignLetters)
    def italic() -> bool: ...

    @property
    def width(self) -> wunumber:
        return sum(l.input.width for l in self.inputs) if self.inputs else 0

    @property
    def height(self) -> wunumber:
        return max(l.input.height for l in self.inputs) if self.inputs else 0

    def __str__(self) -> str:
        return f"Text({self.text})"
