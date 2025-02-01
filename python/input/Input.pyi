#!/usr/bin/env python3

from __future__ import annotations
from typing import overload
from _ty import uint

from transformation.Transformation import Transformation

class Input:
    """
    Represents an `Input` which is a list of frames.

    A frame is a matrix of pixel.

    `1 second` == `24 frames`.

    ::

    def image(filepath: str) -> Input: ...

    ::

    def video(filepath: str) -> Input: ...

    ::

    def text(string: str) -> Input: ...

    ::

    def shape() -> Input: ...
    """

    def add(self) -> None:
        """
        Appends the `frames` of `self` to the `timeline`.
        """
        ...

    def apply(self, *ts: Transformation) -> Input:
        """
        Applies the `Transformations` `ts` to all the `frames` of `self`.
        """
        ...

    def repeat(self, n: uint) -> Input:
        """
        Creates a `new` `Input` made of `n` times `self`.
        """
        ...

    def copy(self) -> Input:
        """
        Creates a `copy` of `self`.
        """
        ...

    def concat(self, i: Input) -> Input:
        """
        Concatenates `i` after `self`.
        """
        ...

    def merge(self, i: Input) -> Input:
        """
        Merges with `i`.

        Each `Input` will have the same ratio on the result.
        """
        ...

    def overlay(self, i: Input) -> Input:
        """
        Overlays `i` on top of `self`.

        `i` has a ratio priority over `self`.
        """
        ...

    @overload
    def __getitem__(self, i: int) -> Input:
        """
        Creates a `reference` of the `frame` `i`.
        """
        ...

    @overload
    def __getitem__(self, s: slice) -> Input:
        """
        Creates a `reference` of the `frames` `s`.
        """
        ...
