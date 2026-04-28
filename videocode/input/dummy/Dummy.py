#!/usr/bin/env python3


from typing import Any

from videocode.context import Any
from videocode.input.input import *
from videocode.utils.funcutils import Any


class Dummy(Input):
    """
    A `Dummy` is a fake `Input` that does nothing but prevent the need to check for None if a var is maybe[Input].
    """

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        object.__setattr__(instance, "meta", Metadata(interface=True))
        return instance

    def __init__(self):
        pass

    def __getattr__(self, name: str) -> Self:
        return self

    def __setattr__(self, name: str, value) -> None:
        pass

    def __call__(self, *args, **kwargs) -> Self:
        return self


type dummy[T] = Dummy | T
