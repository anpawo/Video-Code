#!/usr/bin/env python3


from videocode.shader.ishader import *


class rotation(VertexShader):
    """
    `Rotation` is set to degree.

    # TODO: a position where the rotation should take place from.
    """

    def __init__(self, degree: number):
        self.degree = degree

    def modificator(self, i: Input):
        i.meta.rotation = self.degree
