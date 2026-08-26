#!/usr/bin/env python3

from __future__ import annotations

from typing import Generic
from typing_extensions import TypeVar

from videocode.shader.ishader import *
from videocode.utils.classutils import Maybe

_T1 = TypeVar("_T1", bound=mnbr, default=number)
_T2 = TypeVar("_T2", bound=mnbr, default=number)


class position(VertexShader, Generic[_T1, _T2]):
    _rigidKind = 1
    """
    set the position `x` and `y` of an `Input`.

    - `None` doesn't change the position

    This takes action on all frames instantly, there is no delay.

    For a movement over time, see `moveTo`.
    """

    def __init__(self, x: _T1, y: _T2) -> None:
        self.x = x
        self.y = y
        # since it can be None, some compaapny
        # could be self.p = v2(x, y)
        # TODO: so we could use a setattr(attr) with the VertexShader and so remove the modificators

    def autodestroy(self, i: Input) -> bool:
        # Judged on the CLAIMED components only. A `None` is not a value that
        # happens to match — it is the absence of a claim, so it can never be the
        # reason to keep the shader. Claiming nothing at all is a no-op outright.
        if self.x is None and self.y is None:
            return True
        return (self.x is None or i.meta.position.x == self.x) and (self.y is None or i.meta.position.y == self.y)

    def modify(self, i: Input):
        # A component left `None` is one this effect does NOT CLAIM, and it must
        # reach the stack as a hole rather than as a value.
        #
        # Filling it in from the cursor is what made `moveTo(x=2)` claim the y it
        # was never given: every frame of its window then carried a y, and it
        # overwrote a y animation it knew nothing about. The cursor is still kept
        # current for the 127 places that read `meta`, but only for what was asked
        # for.
        if self.x is not None:
            i.meta.position.x = self.x
        if self.y is not None:
            i.meta.position.y = self.y
