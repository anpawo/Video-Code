#!/usr/bin/env python3

from __future__ import annotations

import videocode.input.shape.text._MarkdownHelper as _helper
from videocode.input.interface.Group import Group
from videocode.input.shape.text.Text import Text
from videocode.ty import *
from videocode.constants import *

__all__ = [
    "Markdown",
]


class Markdown(Group[Text]):
    """
    Render a Markdown file as a vertical stack of left-aligned `Text` blocks.

    v1 scope (block-level only, see `_MarkdownHelper.parseMarkdown`):
    headings (`#`..`######`), `- `/`* ` bullet items, a whole line wrapped in
    `**bold**`/`*italic*`, and plain paragraphs. No inline mixed styling
    within a single line.
    """

    def __init__(
        self,
        filepath: str,
        fontSize: wnumber = 0.4,
        fillColor: rgba = WHITE,
        strokeColor: rgba = BLACK,
        strokeWidth: wufloat = 0.02,
        x: wnumber = -WORLD_OFFSET_X + 1,
        y: wnumber = WORLD_OFFSET_Y - 1,
        lineSpacing: wnumber = 1.3,
    ) -> None:
        texts: list[Text] = []

        currentY = y
        for block in _helper.parseMarkdown(filepath, fontSize):
            texts.append(
                Text(
                    block.text,
                    fontSize=block.fontSize,
                    fillColor=fillColor,
                    strokeColor=strokeColor,
                    strokeWidth=strokeWidth,
                    bold=block.bold,
                    italic=block.italic,
                )
                .position(x=x, y=currentY)
                .align(x=0)
            )
            currentY -= block.fontSize * lineSpacing

        super().__init__(*texts)
