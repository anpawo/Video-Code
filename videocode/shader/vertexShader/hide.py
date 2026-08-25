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
        # Never. `autodestroy` answers from the WRITE CURSOR, and visibility is
        # a discrete state whose value at a frame is set by the last statement
        # in TIME, not the last one typed: `show(start=2)` written before
        # `hide(start=1)` was dropped as a no-op — the input was visible when
        # the line ran — and then hidden for good by a line that came after it
        # in the file and before it on the timeline. Writing it always costs one
        # argument-free entry, and `Context._EXCLUSIVE` keeps a frame down to
        # one of the two.
        return False

    def modify(self, i: Input):
        i.meta.hidden = True
