#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *


class compositionMember(VertexShader):
    """
    Bind an `Input` to the composition layer that flattens it.

    A member is drawn into its composition's isolated layer and nowhere else, so it
    never reaches the frame on its own — which is what makes a composition's fade one
    flat fade instead of a fade per member.

    `layer` travels through the stack as a plain int (`layer.meta.index`),
    already 1:1 with the C++ `_inputs[]` position — the same reference channel
    `matte` uses for its source.

    Users don't apply this directly — `Composition(...)` applies it to every member.
    """

    def __init__(self, layer: Input):
        self.composition = layer.meta.index

    def autodestroy(self, i: Input) -> bool:
        """Idempotent: an input already bound to this composition drops the second binding."""
        return i.meta.compositionIndex == self.composition

    def modify(self, i: Input):
        """Point the input at the composition layer it is drawn into."""
        i.meta.compositionIndex = self.composition
