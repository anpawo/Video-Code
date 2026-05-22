#!/usr/bin/env python3


from videocode.shader.ishader import *


class show(VertexShader):
    """
    Show the `Input`.
    """

    def __init__(self) -> None: ...

    def autodestroy(self, i: Input) -> bool:
        return i.meta.hidden == False

    def modify(self, i: Input):
        i.meta.hidden = False
