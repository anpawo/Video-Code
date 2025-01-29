#!/usr/bin/env python3

from __future__ import annotations
from typing import overload
from _ty import uint

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
        Appends the `frames` of the `Input` to the `timeline`.
        """
        ...

    def apply(self, *t: Transformation) -> Input:
        """
        Applies the `Transformation` `t` to all the `frames` of the `Input`.
        """
        ...

    def repeat(self, n: uint) -> Input:
        """
        Returns a `new` `Input` made of `n` times itself.
        """
        ...

    def copy(self) -> Input:
        """
        Returns a `copy` of itself.
        """
        ...

    def concat(self, i: Input) -> Input:
        """
        Concat itself with `i`.
        """
        ...

    @overload
    def __getitem__(self, i: int) -> Input:
        """
        Returns a `reference` of the `frame` `i`.
        """
        ...

    @overload
    def __getitem__(self, s: slice) -> Input:
        """
        Returns a `reference` of the `frames` `s`.
        """
        ...
