#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.input.input import *


__all__ = ["Video"]


class Video(Input):
    cppName = "Video"
    cppAttrs = {
        "filepath",
    }

    @inputCreation
    def __init__(
        self,
        filepath: str,
    ) -> None:
        self.filepath = filepath
