#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.input.input import *


__all__ = ["Video"]


class Video(Input):
    cppName = "Video"
    cppAttrs = {
        "filepath",
        "cuts",
    }

    @inputCreation
    def __init__(
        self,
        filepath: str,
        cuts: list[frame | tuple[frame, frame]] = [],
    ) -> None:
        """
        `cuts` are ranges of source-video frames to skip during playback —
        either a single frame index `n` (shorthand for `(n, n + 1)`) or a
        `(start, end)` pair cutting `[start, end)`.
        """
        self.filepath = filepath
        self.cuts = [c if isinstance(c, tuple) else (c, c + 1) for c in cuts]
