#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.input.Input import *


class video(Input):
    @inputCreation
    def __init__(
        self,
        filepath: str,
    ) -> None:
        self.filepath = filepath
