#!/usr/bin/env python3

#
# Types
#

import types

from constants import *
from typing import Any, TypeAliasType, Union, get_origin, get_args
from videocode.utils.logger import *


def upperFirst(s: str):
    return s[0].upper() + s[1:]


def floatRange(start: number, end: number, step: number):

    def rangeGenerator(start, end, step):
        n = start
        while n < end:
            yield n
            n += step

    return rangeGenerator(start, end, step)
