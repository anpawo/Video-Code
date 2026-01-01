#!/usr/bin/env python3


from videocode.constants import *
from videocode.utils.decorators import inputCreation
from videocode.input.input import *


class text(Input):
    @inputCreation
    def __init__(
        self,
        text: str,
        fontSize: ufloat = 3,
        color: rgba = WHITE,
        fontThickness: maybe[ufloat] = None,
    ):
        self.text = text
        self.fontSize = fontSize
        self.color = color
        self.fontThickness = fontThickness or fontSize * 2
