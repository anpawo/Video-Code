#!/usr/bin/env python3

from __future__ import annotations

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


def size(shape: str, name: str, value: float) -> float:
    """
    A dimension that is not one, refused by name instead of swallowed.

    `Circle(radius=-1)` used to build a circle of radius 1: the sign vanished
    into `cos`/`sin` and the author got a picture that did not match the code,
    with nothing said. The type aliases spell the rule out — `wufloat` is an
    unsigned world float — and nothing was enforcing it.
    """
    if value < 0:
        raise ValueError(f"{shape}({name}={value}): a {name} cannot be negative. Use {abs(value)} if that is what you meant.")
    return value
