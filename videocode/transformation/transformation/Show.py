#!/usr/bin/env python3

from videocode.Constant import *
from videocode.Global import Metadata
from videocode.transformation.Transformation import Transformation


class show(Transformation):
    """
    Show the `Input`.
    """

    def __init__(self) -> None: ...

    def modificator(self, meta: Metadata):
        meta.hidden = False
