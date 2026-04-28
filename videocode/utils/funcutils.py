#!/usr/bin/env python3

#
# Types
#

import types

from constants import *
from typing import Any, TypeAliasType, Union, get_origin, get_args
from videocode.utils.logger import *


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
