#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *


class show(VertexShader):
    """
    Show the `Input`.
    """

    def __init__(self) -> None: ...

    def autodestroy(self, i: Input) -> bool:
        return False  # never — see hide.autodestroy

    def modify(self, i: Input):
        i.meta.hidden = False
