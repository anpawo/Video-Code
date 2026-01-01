#!/usr/bin/env python3

from videocode.effect.effect import *
from videocode.constants import number


class rotate(Transformation):
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
