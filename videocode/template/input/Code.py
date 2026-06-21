#!/usr/bin/env python3

from __future__ import annotations

from videocode.color import rgba
from videocode.input.shape.text.Text import Text
from videocode.shader.vertexShader.align import align
from videocode.shader.vertexShader.args import args as _args
from videocode.ty import *
from videocode.constants import *

__all__ = ["Code"]

_default = rgba("#e6edf3")


class Code(Text):
    def __init__(self, text: str, fontSize: wnumber = 0.2):
        super().__init__(text, fontSize=fontSize, fontFamily="Menlo", fillColor=WHITE)
        self.syntaxColor()
        self.apply(align(x=0, y=0.5), offset=0)

    def syntaxColor(self) -> None:
        from pygments import lex
        from pygments.lexers import PythonLexer
        from pygments.styles import get_style_by_name
        from pygments.token import Token

        source = self.text
        style = get_style_by_name("github-dark")
        # Pygments' github-dark diverges from GitHub's actual theme on these tokens — override to default.
        overrides = {Token.Name.Namespace, Token.Operator}
        tokens = list(lex(source, PythonLexer()))

        callPositions: set[int] = set()
        i = 0
        p = 0
        while i < len(tokens):
            ttype, value = tokens[i]
            if ttype in Token.Name:
                j = i + 1
                while j < len(tokens) and tokens[j][0] in Token.Text:
                    j += 1
                if j < len(tokens) and tokens[j][1] == "(":
                    callPositions.add(p)
            p += len(value)
            i += 1

        charColors: list[rgba] = [_default] * len(source)
        pos = 0
        for ttype, value in tokens:
            if pos in callPositions:
                colorHex = "d2a8ff"  # purple — callable
            elif ttype in Token.Name and value.isupper():
                colorHex = "79c0ff"  # blue — ALL_CAPS constant
            elif ttype in overrides:
                colorHex = None
            else:
                colorHex = style.style_for_token(ttype).get("color")
            color = rgba("#" + colorHex) if colorHex else _default
            for i in range(pos, min(pos + len(value), len(source))):
                charColors[i] = color
            pos += len(value)

        letterColors = [color for char, color in zip(source, charColors) if not char.isspace()]
        for letter, color in zip(self.inputs, letterColors):
            letter.apply(_args("fillColor", color))

    def animateIn(self) -> Self:
        self.typeIn(delay=SINGLE_FRAME / 1.3)
        return self
