#!/usr/bin/env python3

from videocode.constants import *
from videocode.effect.effect import *


class hide(Transformation):
    """
    Hide the `Input`.
    """

    def __init__(self) -> None: ...

    def modificator(self, i: Input):
        i.meta.hidden = True
