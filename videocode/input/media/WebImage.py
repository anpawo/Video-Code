#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.input.Input import *


class webImage(Input):
    @inputCreation
    def __init__(
        self,
        url: url,
    ):
        self.url = url
