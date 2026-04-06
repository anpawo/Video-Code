#!/usr/bin/env python3


from videocode.constants import *
from videocode.utils.decorators import inputCreation
from videocode.input.input import *


class Text(Input):
    @inputCreation
    def __init__(
        self,
        text: str,
        fontSize: wufloat = 0.5,
        color: rgba = WHITE,
    ):
        self.text = text
        self.fontSize = fontSize
        self.color = color
