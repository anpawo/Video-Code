#!/usr/bin/env python3

from __future__ import annotations

import videocode.input.shape.text._SubtitleHelper as _helper
from videocode.input.interface.Group import Group
from videocode.input.shape.text.Text import Text
from videocode.ty import *
from videocode.constants import *


__all__ = [
    "Subtitles",
]


class Subtitles(Group[Text]):
    """
    Render a `.srt` subtitle file as timed `Text` inputs, one per cue line.

    Each line is hidden by default and only shown between its cue's start
    and end timestamps (in seconds, as read from the file).
    """

    def __init__(
        self,
        filepath: str,
        fontSize: wnumber = 0.4,
        fillColor: rgba = WHITE,
        strokeColor: rgba = BLACK,
        strokeWidth: wufloat = 0.02,
        y: wnumber = -WORLD_OFFSET_Y + 0.6,
        lineSpacing: wnumber = 0.5,
    ) -> None:
        texts: list[Text] = []

        for cue in _helper.parseSRT(filepath):
            lines = cue.text.splitlines()
            for i, line in enumerate(lines):
                texts.append(
                    Text(line, fontSize=fontSize, fillColor=fillColor, strokeColor=strokeColor, strokeWidth=strokeWidth)
                    .position(x=0, y=y + (len(lines) - 1 - i) * lineSpacing)
                    .hide(start=0)
                    .show(start=cue.start)
                    .hide(start=cue.end)
                )

        super().__init__(*texts)
