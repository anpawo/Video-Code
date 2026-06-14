#!/usr/bin/env python3

from __future__ import annotations

import re

from videocode.ty import *

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET_RE = re.compile(r"^[-*]\s+(.*)$")
_BOLD_RE = re.compile(r"^\*\*(.*)\*\*$")
_ITALIC_RE = re.compile(r"^\*(.*)\*$")

# fontSize multipliers for heading levels 1-6, relative to the base paragraph size.
_HEADING_SCALE = {1: 2.0, 2: 1.7, 3: 1.4, 4: 1.2, 5: 1.1, 6: 1.0}


class MarkdownBlock:
    __slots__ = ("text", "fontSize", "bold", "italic")

    def __init__(self, text: str, fontSize: wnumber, bold: bool, italic: bool) -> None:
        self.text = text
        self.fontSize = fontSize
        self.bold = bold
        self.italic = italic


def parseMarkdown(filepath: str, fontSize: wnumber) -> list[MarkdownBlock]:
    """
    Parse a Markdown file into a flat list of block-level `MarkdownBlock`s.

    v1 scope (block-level only, one block per non-empty line):
    - `#`..`######` headings — larger `fontSize`, bold
    - `- `/`* ` bullet list items — rendered with a "• " prefix
    - a whole line wrapped in `**...**` or `*...*` — bold/italic paragraph
    - anything else — a plain paragraph

    Blank lines are skipped (they only affect spacing between blocks, handled
    by the caller). No inline mixed styling within a single line.
    """
    with open(filepath, "r", encoding="utf-8") as file:
        lines = file.read().splitlines()

    blocks: list[MarkdownBlock] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        heading = _HEADING_RE.match(line)
        if heading is not None:
            level = len(heading.group(1))
            blocks.append(MarkdownBlock(heading.group(2).strip(), fontSize * _HEADING_SCALE.get(level, 1.0), True, False))
            continue

        bullet = _BULLET_RE.match(line)
        if bullet is not None:
            blocks.append(MarkdownBlock(f"• {bullet.group(1).strip()}", fontSize, False, False))
            continue

        bold = _BOLD_RE.match(line)
        if bold is not None:
            blocks.append(MarkdownBlock(bold.group(1).strip(), fontSize, True, False))
            continue

        italic = _ITALIC_RE.match(line)
        if italic is not None:
            blocks.append(MarkdownBlock(italic.group(1).strip(), fontSize, False, True))
            continue

        blocks.append(MarkdownBlock(line, fontSize, False, False))

    return blocks
