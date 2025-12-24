#!/usr/bin/env python3

from videocode.Global import Metadata
from videocode.transformation.Transformation import Transformation
from videocode.Constant import number


class rotate(Transformation):
    """
    `Rotate` by degree.

    It may change it's original width and height.

    # TODO: a position where the rotation should take place from.
    """

    def __init__(
        self,
        degree: number,
    ):
        self.degree = degree

    def modificator(self, meta: Metadata):
        meta.rotation = self.degree
