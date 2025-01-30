#!/usr/bin/env python3

from Transformation import Transformation

from .._ty import *

def fadeIn(fromSide: side, n: int, /) -> Transformation:
    """
    `Fade in`  from `side` in `n` frames.
    """
    ...

def fadeOut(fromSide: side, n: int, /) -> Transformation:
    """
    `Fade out` from `side` in `n` frames.
    """
    ...
