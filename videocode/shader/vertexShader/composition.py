#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *


class composition(VertexShader):
    """
    Mark an `Input` as a composition layer — the one layer a `Composition` renders as.

    The input is never drawn on its own. Its MEMBERS (the inputs carrying
    `compositionMember` for it) are flattened into a single layer instead of onto the
    frame, and that layer is what this input's opacity, effects and matte
    apply to. Presence is the whole signal — there are no arguments; the
    renderers key off `meta.isComposition`.

    Users don't apply this directly — `Composition(...)` (input/interface/Composition.py)
    applies it to the layer it builds, mirroring how `AdjustmentLayer` applies
    its own marker.
    """

    def __init__(self):
        pass

    def autodestroy(self, i: Input) -> bool:
        """Idempotent: an input already marked as a composition layer drops the second mark."""
        return i.meta.isComposition

    def modify(self, i: Input):
        """Flag the input as the layer its composition's members are flattened into."""
        i.meta.isComposition = True
