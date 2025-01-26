#!/usr/bin/env python3

from __future__ import annotations
from typing import overload, Tuple

from transformation.Transformation import Transformation

class Input:
    """
    Represents an `Input`. ::

        def image(filepath: str) -> int: ...
        def video(filepath: str) -> int: ...
        def text(text: str) -> int: ...
    """

    @overload
    def apply(self, t: Transformation) -> Input: ...
    @overload
    def apply(self, __fromStartToEnd: Tuple[int, int]) -> Input: ...
    @overload
    def apply(self, __fromStart: int) -> Input: ...
