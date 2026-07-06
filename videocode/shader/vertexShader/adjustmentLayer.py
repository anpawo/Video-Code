#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *


class adjustmentLayer(VertexShader):
    """
    Mark an `Input` as an After Effects-style adjustment layer.

    The input is never drawn on its own. Instead, any fragment effects applied
    to it grade the flattened composite of every mesh drawn BELOW it in z-order.
    Presence is the whole signal — there are no arguments; the renderer keys off
    `meta.isAdjustmentLayer`.

    Users don't apply this directly — `AdjustmentLayer()` (input/AdjustmentLayer.py)
    applies it in its constructor, mirroring how `Shadow` auto-applies its blur.
    """

    def __init__(self):
        pass

    def autodestroy(self, i: Input) -> bool:
        # Idempotent: a second application changes nothing.
        return i.meta.isAdjustmentLayer

    def modify(self, i: Input):
        i.meta.isAdjustmentLayer = True
