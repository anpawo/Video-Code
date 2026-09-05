#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *


class comp(VertexShader):
    """
    Mark an `Input` as a comp layer — the one layer a `Comp` renders as.

    The input is never drawn on its own. Its MEMBERS (the inputs carrying
    `compMember` for it) are flattened into a single layer instead of onto the
    frame, and that layer is what this input's opacity, effects and matte
    apply to. Presence is the whole signal — there are no arguments; the
    renderers key off `meta.isComp`.

    Users don't apply this directly — `Comp(...)` (input/interface/Comp.py)
    applies it to the layer it builds, mirroring how `AdjustmentLayer` applies
    its own marker.
    """

    def __init__(self):
        pass

    def autodestroy(self, i: Input) -> bool:
        """Idempotent: an input already marked as a comp layer drops the second mark."""
        return i.meta.isComp

    def modify(self, i: Input):
        """Flag the input as the layer its comp's members are flattened into."""
        i.meta.isComp = True
