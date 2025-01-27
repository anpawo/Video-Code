#!/usr/bin/env python3

from __future__ import annotations
from typing import overload, Tuple

from transformation.Transformation import Transformation

class Input:
    """
    Represents an `Input` which is a list of frame.

    A frame is a matrix of pixel.

    ::

        def image(filepath: str) -> Input: ...
        def video(filepath: str) -> Input: ...
        def text(string: str) -> Input: ...
        def shape() -> Input: ...
    """

    def apply(self, t: Transformation) -> Input:
        """
        Applies the `Transformation` `t` to the `Input`.
        """
        ...

    def repeat(self, n: int) -> Input:
        """
        Repeat itself `n` times.
        """
        ...

    @overload
    def __getitem__(self, i: int) -> Input:
        """
        Extracts `one frame`.
        """
        ...

    @overload
    def __getitem__(self, s: slice) -> Input:
        """
        Extracts a `slice of frames`.
        """
        ...
