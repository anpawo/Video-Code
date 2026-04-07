#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.input.input import *


class audio(Input):

    @inputCreation
    def __init__(
        self,
        filepath: str,
        volume: float = 1.0,
    ) -> None:
        self.filepath = filepath
        self.volume = volume
