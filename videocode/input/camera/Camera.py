#!/usr/bin/env python3


from videocode.input.Input import *
from videocode.transformation.setter.SetPosition import setPosition


class camera(Input):
    """
    The `Camera` represents what we see of the video.

    The `Camera` can move and `Shaders` can be applied to it.
    """

    """
    The instance is unique for the `Camera`
    """
    _instance: None | Self = None

    """
    The index of the `Camera` is always `-1`
    """
    _index = -1

    def __new__(cls, *args, **kwargs) -> Self:
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls._instance.index = cls._index
            cls._instance.meta = Metadata(x=0, y=0)
        return cls._instance

    def __init__(self):
        pass
