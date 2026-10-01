#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class letterbox(FragmentShader):
    """
    Black bars so the visible area matches `ratio` (width / height) — bars
    top/bottom when `ratio` is wider than the frame, left/right when it is
    narrower. Frame-based: it reads the whole frame, not the input's own box.

    Example: `video.apply(letterbox(2.39), duration=3)`  # cinemascope
    """

    def __init__(self, ratio: number = 2.39):
        self.ratio = ratio
