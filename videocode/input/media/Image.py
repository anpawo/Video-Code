#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.input.input import *


class Image(Input):
    cppAttrs = {
        "filepath",
    }

    @inputCreation
    def __init__(
        self,
        filepath: str,
    ):
        self.meta.name = "Image"

        self.filepath = filepath
