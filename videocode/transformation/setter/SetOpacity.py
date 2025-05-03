#!/usr/bin/env python3

from videocode.Constant import *
from videocode.Global import Metadata
from videocode.transformation.setter.Setter import Setter


class setOpacity(Setter):
    """
    set the opacity of an `Input`, between [0, 255].
    """

    def __init__(self, opacity: uint) -> None:
        self.opacity = opacity

    def modificator(self, meta: Metadata):
        meta.opacity = self.opacity
