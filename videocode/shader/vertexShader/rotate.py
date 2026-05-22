#!/usr/bin/env python3


from videocode.shader.ishader import *


class rotation(VertexShader):
    """
    `Rotation` is set to degree.

    The rotation can take place from another place than the center by using Offset.
    """

    def __init__(self, degree: number):
        self.degree = degree

    def autodestroy(self, i: Input) -> bool:
        return i.meta.rotation == self.degree

    def modify(self, i: Input):
        i.meta.rotation = self.degree
