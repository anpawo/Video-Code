#!/usr/bin/env python3


from typing import Self, cast
from videocode.context import Metadata
from videocode.input.input import Input


class Interface(Input):

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.meta = Metadata(interface=True)
        return instance
