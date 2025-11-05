#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self
from videocode.Constant import *
from videocode.transformation.Transformation import Transformation


class Setter(Transformation, ABC):
    """
    A `Setter`, is a kind of `Transformation`.

    Setters are persistent unless overridden and they take action instantly on the current frame of the `Input`, not over time.
    The reason for that is that they affect the metadata of the `Input`.
    """

    @abstractmethod
    def __init__(self) -> None: ...

    def __new__(cls, *args, **kwargs) -> Self:
        instance = super().__new__(cls)
        instance.duration = default(0)
        return instance


class setArgument(Setter):
    """
    `setArgument` is a setter that modifies the base of an `Input` before any other transformation, e.g. the radius of a circle.
    """

    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self.value = value
