#!/usr/bin/env python3

from videocode.constants import *
from videocode.shader.ishader import *


class show(VertexShader):
    """
    Show the `Input`.
    """

    def __init__(self) -> None: ...

    def modificator(self, i: Input):
        i.meta.hidden = False
