#!/usr/bin/env python3

from __future__ import annotations

from enum import IntEnum

from videocode.shader.ishader import *


class BlendMode(IntEnum):
    """
    Compositing mode of an `Input` — how its pixels combine with whatever is
    already drawn behind it. Values match the C++ pipeline index
    (`BlendModes.hpp`) and `Metadata.blendMode` directly (`BlendMode` is an
    `IntEnum`, so it serializes to the JSON stack as a plain int).

    - `NORMAL`   : standard alpha blend (default)
    - `MULTIPLY` : darkens (source × destination)
    - `SCREEN`   : lightens (inverse-multiply)
    - `ADD`      : linear dodge, clips toward white

    Overlay is intentionally unsupported — it requires reading the destination
    pixel in the fragment shader, which the fixed-function blend pipeline cannot
    express.
    """

    NORMAL = 0
    MULTIPLY = 1
    SCREEN = 2
    ADD = 3


class blendMode(VertexShader):
    def __init__(self, mode: BlendMode):
        self.mode = mode

    def autodestroy(self, i: Input) -> bool:
        return i.meta.blendMode == self.mode

    def modify(self, i: Input):
        i.meta.blendMode = self.mode
