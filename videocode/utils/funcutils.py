#!/usr/bin/env python3

#
# Types
#

from constants import *
from typing import Any, get_origin, get_args


def getValueByPriority(c: Any, var: Any, name: str) -> sec:
    """
    Priority of arguments

    Transformation's Value > Given Value > Function's Default
    """
    if hasattr(c, name) and isinstance(getattr(c, name), int | float):
        return getattr(c, name)
    elif isinstance(var, int | float):
        return var
    elif hasattr(c, name) and isinstance(getattr(c, name), default):
        return getattr(c, name).defaultValue
    elif isinstance(var, default):
        return var.value
    else:
        raise ValueError(var)


def upperFirst(s: str):
    return s[0].upper() + s[1:]


def fromWorlToScreen(annotations: dict[str, type], values: dict[str, Any]) -> dict:
    adapt = [wint, wuint, wfloat, wufloat]

    def shouldScale(t) -> bool:
        if t in adapt:
            return True

        origin = get_origin(t)
        if origin is None:
            return False

        for arg in get_args(t):
            if shouldScale(arg):
                return True
        return False

    for k, v in values.items():
        if shouldScale(annotations[k]):
            values[k] = v * WORLD_TO_SCREEN_RATIO

    return values


