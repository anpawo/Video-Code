#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *


class rotation(VertexShader):
    _rigidKind = 2
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
