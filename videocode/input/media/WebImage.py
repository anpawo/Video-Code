#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.input.input import *


class WebImage(Input):
    @inputCreation
    def __init__(
        self,
        url: url,
    ):
        self.meta.name = "WebImage"

        self.url = url
