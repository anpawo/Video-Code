#!/usr/bin/env python3


from abc import abstractmethod

from videocode.input.input import Input
from videocode.utils.decorators import inputCreation, setAttrOn
from videocode.ty import *
from videocode.constants import *


class Polygon(Input):
    @inputCreation
    def __init__(
        self,
        points: list[point],
        fillColor: rgba,
        strokeColor: rgba,
        strokeWidth: wufloat,
        cornerRadius: percent,  # percent 0-100, 100 = circle on a square
    ):
        self.meta.name = "Polygon"

        self.points = points
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth
        self.cornerRadius = min(max(cornerRadius, 0), 100)

    def generatePoints(self) -> list[point]:
        return self.points
