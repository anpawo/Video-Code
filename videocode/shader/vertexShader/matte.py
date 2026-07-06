#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *


class matte(VertexShader):
    """
    Use another `Input`'s alpha as a track matte (mask) for this `Input`.

    The masked input (A) is only visible where the `source` input (B) has
    coverage — think a `Video` clipped to a `Text` silhouette. Standard editor
    track-matte semantics: B is consumed purely as a mask and is NOT drawn
    separately in the final composite.

    `source` travels through the stack as a plain int (`source.meta.index`),
    which is already 1:1 with the C++ `_inputs[]` position — the renderer
    resolves it back to B's finished layer at draw time (see the 2-sampler
    matte-combine pass in both renderers).
    """

    def __init__(self, source: Input):
        self.source = source.meta.index

    def autodestroy(self, i: Input) -> bool:
        return i.meta.matteSource == self.source

    def modify(self, i: Input):
        i.meta.matteSource = self.source
