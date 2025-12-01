#!/usr/bin/env python3


from videocode.Decorators import inputCreation
from videocode.input.Input import *


class webImage(Input):
    url: str

    @inputCreation
    def __init__(
        self,
        url: str,
    ): ...
