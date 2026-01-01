#!/usr/bin/env python3


from videocode.input.input import *
from videocode.effect.transformation.position import position


class camera(Input):
    """
    The `Camera` represents what we see of the video.

    The `Camera` can move and `Transformations` can be applied to it.

    !!! Warning !!!
    The Camera cannot work because it would crop stuff on scale downs
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
            cls._instance.meta = Metadata(cls._instance.__dict__, interface=True)
            cls._instance.meta.index = cls._index
        return cls._instance

    def __init__(self):
        pass
