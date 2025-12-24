#!/usr/bin/env python3

from videocode.Constant import *
from videocode.Global import Metadata
from videocode.transformation.Transformation import Transformation


class hide(Transformation):
    """
    Hide the `Input`.
    """

    def __init__(self) -> None: ...

    def modificator(self, meta: Metadata):
        meta.hidden = True
