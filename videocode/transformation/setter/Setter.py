#!/usr/bin/env python3

from __future__ import annotations
from typing import Self
from videocode.Constant import *
from videocode.transformation.Transformation import Transformation


class Setter(Transformation):
    """
    Represents a `Setter`, a kind of `Transformation`.

    Setters are persistent and they take action instantly on the `Input` if called through `<Input>.set<Setter>()` or if `self.enableSetter()` is called.

    Otherwise, if used through `<Input>.apply(<Setter>())`, they take action on the next frame.
    """

    duration: sec | default

    isSetter: bool

    def __new__(cls, *args, **kwargs) -> Self:
        instance = super().__new__(cls)
        instance.isSetter = False
        return instance

    def enableSetter(self) -> Self:
        self.isSetter = True
        return self
