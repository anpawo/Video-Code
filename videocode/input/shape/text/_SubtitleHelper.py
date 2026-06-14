#!/usr/bin/env python3

from __future__ import annotations

import re


_TIMESTAMP_RE = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{3})")


class SubtitleCue:
    __slots__ = ("start", "end", "text")

    def __init__(self, start: float, end: float, text: str) -> None:
        self.start = start
        self.end = end
        self.text = text


def parseTimestamp(timestamp: str) -> float:
    match = _TIMESTAMP_RE.match(timestamp.strip())
    if match is None:
        raise ValueError(f"invalid SRT timestamp: {timestamp!r}")
    hours, minutes, seconds, millis = (int(g) for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def parseSRT(filepath: str) -> list[SubtitleCue]:
    """
    Parse a `.srt` subtitle file into a list of `SubtitleCue`s.

    Each cue's index line is optional — only the `start --> end` timing line
    and the following text lines are required.
    """
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()

    cues: list[SubtitleCue] = []
    for block in re.split(r"\n\s*\n", content.strip()):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        timingIdx = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timingIdx is None:
            continue

        start, end = (part.strip() for part in lines[timingIdx].split("-->"))
        text = "\n".join(lines[timingIdx + 1 :])
        cues.append(SubtitleCue(parseTimestamp(start), parseTimestamp(end), text))

    return cues
