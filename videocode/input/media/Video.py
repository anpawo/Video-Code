#!/usr/bin/env python3


from videocode.utils.decorators import inputCreation
from videocode.input.input import *


class video(Input):
    filepath: str

    @inputCreation
    def __init__(
        self,
        filepath: str,
    ) -> None: ...
