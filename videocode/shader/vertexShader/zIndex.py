#!/usr/bin/env python3

from __future__ import annotations

from videocode.context import Context
from videocode.shader.ishader import *


class zIndex(VertexShader):
    """
    Set the render order of an `Input`.

    Inputs are drawn in ascending `zIndex` order (lower = further behind).
    Defaults to creation order, so inputs don't tie unless `zIndex` is set
    explicitly. When two inputs share a `zIndex`, the one whose `zIndex` was
    changed most recently wins (renders on top).
    """

    def __init__(self, zIndex: int):
        self.zIndex = zIndex

    def autodestroy(self, i: Input) -> bool:
        # Never autodestroy, even if `zIndex` is unchanged: re-applying the
        # same value still bumps `zOrderSeq`, which is what wins zIndex ties
        # (most recently changed wins). Skipping here would silently drop
        # that "I changed more recently" signal.
        return False

    def modify(self, i: Input):
        i.meta.zIndex = self.zIndex
        i.meta.zOrderSeq = Context.nextZOrderSeq()
        self.zOrderSeq = i.meta.zOrderSeq
