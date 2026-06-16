#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING
from videocode.shader.ishader import VertexShader


if TYPE_CHECKING:
    from videocode.input.input import Input


class hide(VertexShader):
    """
    Hide the `Input`.
    """

    def __init__(self) -> None: ...

    def autodestroy(self, i: Input) -> bool:
        return i.meta.hidden == True

    def modify(self, i: Input):
        i.meta.hidden = True
