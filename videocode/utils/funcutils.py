#!/usr/bin/env python3

#
# Types
#


from functools import lru_cache

from videocode.constants import *
from videocode.utils.logger import *


@lru_cache(maxsize=None)
def upperFirst(s: str):
    return s[0].upper() + s[1:]


def floatRange(start: number, end: number, step: number):

    def rangeGenerator(start, end, step):
        n = start
        while n < end:
            yield n
            n += step

    return rangeGenerator(start, end, step)


def darken(c: rgba):
    return c | 0.75 | BLACK | (BLACK | 0.7)


def lighten(c: rgba):
    return c | 0.75 | BLACK | GRAY_10


def ppDict(d: dict) -> str:
    """
    Pretty Print a Dict
    """
    s = ""
    for k, v in d.items():
        s += f"{k}:\n\t{v}\n"
    return s
