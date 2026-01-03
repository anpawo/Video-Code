#!/usr/bin/env python3

from videocode.constants import number
from videocode.shader.ishader import *


class rotate(VertexShader):
    """
    `Rotate` by degree.

    # TODO: a position where the rotation should take place from.
    """

    def __init__(
        self,
        degree: number,
    ):
        self.degree = degree

    def modificator(self, i: Input):
        i.meta.rotation = self.degree
