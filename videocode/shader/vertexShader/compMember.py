#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *


class compMember(VertexShader):
    """
    Bind an `Input` to the comp layer that flattens it.

    A member is drawn into its comp's isolated layer and nowhere else, so it
    never reaches the frame on its own — which is what makes a comp's fade one
    flat fade instead of a fade per member.

    `layer` travels through the stack as a plain int (`layer.meta.index`),
    already 1:1 with the C++ `_inputs[]` position — the same reference channel
    `matte` uses for its source.

    Users don't apply this directly — `Comp(...)` applies it to every member.
    """

    def __init__(self, layer: Input):
        self.comp = layer.meta.index

    def autodestroy(self, i: Input) -> bool:
        """Idempotent: an input already bound to this comp drops the second binding."""
        return i.meta.compIndex == self.comp

    def modify(self, i: Input):
        """Point the input at the comp layer it is drawn into."""
        i.meta.compIndex = self.comp
