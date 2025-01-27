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

    def add(self) -> None:
        """
        Append the frames of the `Input` to the timeline.
        """
        ...

    def apply(self, t: Transformation) -> Input:
        """
        Applies the `Transformation` `t` to the `Input`.
        """
        ...

    def repeat(self, n: int) -> Input:
        """
        Return a new array of size `n` with `self` as each elements.
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
