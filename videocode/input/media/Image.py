#!/usr/bin/env python3


from videocode.Decorators import inputCreation
from videocode.input.Input import *


class image(Input):
    filepath: str

    @inputCreation
    def __init__(
        self,
        filepath: str,
    ) -> None: ...
