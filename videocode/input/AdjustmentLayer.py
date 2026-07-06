#!/usr/bin/env python3

from __future__ import annotations

# Imported precisely (not `from videocode import *`) because this module is
# pulled in during package init via input/_inputs.py — a star import of the
# package would be circular.
from videocode.constants import WORLD_HEIGHT, WORLD_WIDTH, TRANSPARENT
from videocode.input.shape.Rectangle import Rectangle
from videocode.shader.vertexShader.adjustmentLayer import adjustmentLayer


class AdjustmentLayer(Rectangle):
    """
    An After Effects-style adjustment layer.

    A full-frame, invisible `Input` whose applied fragment effects grade the
    flattened composite of every layer drawn BELOW its zIndex — instead of any
    geometry of its own (it has none that is ever painted).

        AdjustmentLayer().zIndex(5).apply(grayscale(), duration=...)

    grades every layer with zIndex < 5, leaving anything at/above 5 untouched.
    Multiple adjustment layers stack: each grades everything below it, including
    an earlier adjustment layer's already-graded result.

    Attach effects with the ordinary `.apply(effect)` used by every `Input` — the
    only new API is the layer itself. It auto-applies the `adjustmentLayer`
    marker shader in its constructor (mirroring how `Shadow` auto-applies its
    blur), which sets `meta.isAdjustmentLayer`; the renderers do the rest.

    The full-frame size matters for bbox-driven effects (crop / vignette resolve
    their region from the layer's screen bbox), even though the geometry is never
    drawn.
    """

    def __init__(self):
        super().__init__(
            width=WORLD_WIDTH,
            height=WORLD_HEIGHT,
            fillColor=TRANSPARENT,
            strokeColor=TRANSPARENT,
            strokeWidth=0,
        )
        self.apply(adjustmentLayer())
