#!/usr/bin/env python3


from videocode.constants import *
from videocode.utils.decorators import inputCreation
from videocode.input.input import *


class Text(Input):
    cppAttrs = {
        "text",
        "fontSize",
        "fillColor",
    }

    @inputCreation
    def __init__(
        self,
        text: str,
        fontSize: wufloat = 0.5,
        fillColor: rgba = WHITE,
    ):
        self.meta.name = "Text"

        self.text = text
        self.fontSize = fontSize
        self.fillColor = fillColor
