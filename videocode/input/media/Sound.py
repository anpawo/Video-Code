#!/usr/bin/env python3

from __future__ import annotations

from videocode.input.input import Input
from videocode.utils.decorators import inputCreation
from videocode.ty import *


__all__ = ["Sound"]


class Sound(Input):
    """
    A purely auditory input — adds an audio track to the output video.

    `start` is when the track begins playing in the output timeline (seconds).
    `trimStart`/`trimEnd` cut the source file's own audio to `[trimStart, trimEnd)`
    (seconds, `trimEnd=None` plays to the end of the source).
    `volume` is a linear multiplier (1.0 = unchanged).

    Multiple `Sound` inputs are mixed together in the output.
    """

    cppName = "Sound"
    cppAttrs = {"filepath", "volume", "delay", "trimStart", "trimEnd"}

    @inputCreation
    def __init__(
        self,
        filepath: str,
        start: sec = 0,
        volume: ufloat = 1.0,
        trimStart: sec = 0,
        trimEnd: maybe[sec] = None,
    ) -> None:
        self.filepath = filepath
        self.delay = start
        self.volume = volume
        self.trimStart = trimStart
        self.trimEnd = trimEnd
