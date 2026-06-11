#!/usr/bin/env python3


import math
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

    def _distributeGradientColor(self, attr: str) -> None:
        """
        Assigns `getattr(self, attr)` (`fillColor` or `strokeColor`) to each
        letter. A plain `rgba` is broadcast as-is, but a `LinearGradient` is
        sliced per letter so the gradient spans the whole word — like CSS
        `background-clip: text` — instead of repeating across each letter's
        own bounding box.
        """
        letters = self.inputs[: len(self.text)]
        if not letters:
            return

        color = getattr(self, attr)
        if not isinstance(color, LinearGradient):
            for l in letters:
                setattr(l.input, attr, color)
            return

        data = _helper.buildLetterData(self.text, self.fontSize, self.fontFamily, self.bold, self.italic)

        angleRad = math.radians(color.angle)
        dx, dy = math.cos(angleRad), math.sin(angleRad)

        def projRange(x: float, y: float, w: float, h: float) -> tuple[float, float]:
            projs = (x * dx + y * dy, (x + w) * dx + y * dy, x * dx + (y + h) * dy, (x + w) * dx + (y + h) * dy)
            return min(projs), max(projs)

        ranges = [projRange(x, y, l.input.width, l.input.height) for l, (_, x, y) in zip(letters, data)]
        globalMin = min(r[0] for r in ranges)
        globalMax = max(r[1] for r in ranges)
        globalRange = globalMax - globalMin

        for l, (letterMin, letterMax) in zip(letters, ranges):
            if globalRange < 1e-9:
                setattr(l.input, attr, color.colorAt(0))
            else:
                t0 = (letterMin - globalMin) / globalRange * 100
                t1 = (letterMax - globalMin) / globalRange * 100
                setattr(l.input, attr, color.slice(t0, t1))

    def _distributeFillColor(self) -> None:
        self._distributeGradientColor("fillColor")

    def _distributeStrokeColor(self) -> None:
        self._distributeGradientColor("strokeColor")

    @prop(onSet=_distributeFillColor)
    def fillColor() -> rgba: ...

    @prop(onSet=_distributeStrokeColor)
    def strokeColor() -> rgba: ...

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

        self._distributeFillColor()
        self._distributeStrokeColor()

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
