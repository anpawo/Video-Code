#!/usr/bin/env python3

#
# Types
#

from typing import Any
from Constant import *

type t = Union[ufloat, uint, default]

class default[T]:
    """
    Default value to specify that a value is the default one and should be overriden by a given one.
    """

    def __init__(self, defaultValue: T) -> None:
        self.defaultValue = defaultValue

    def __str__(self) -> str:
        return f"default({self.defaultValue})"

def getValueByPriority(c: Any, value: Any, name: str) -> sec:
    """
    Priority of arguments

    Transformation's Default > Given Value > Function's Default
    """
    if hasattr(c, name) and isinstance(getattr(c, name), int | float):
        return getattr(c, name)
    elif isinstance(value, int | float):
        return value
    elif hasattr(c, name) and isinstance(getattr(c, name), default):
        return getattr(c, name).defaultValue
    elif isinstance(value, default):
        return value.defaultValue
    else:
        raise ValueError(value)

def upperFirst(s: str):
    return s[0].upper() + s[1:]
