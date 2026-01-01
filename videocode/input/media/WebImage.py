#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.input.input import *


class webImage(Input):
    url: str

    @inputCreation
    def __init__(
        self,
        url: str,
    ): ...
