#!/usr/bin/env python3


import copy


from typing import Callable
from videocode.input.input import *


type Callback = Callable[[Any, Any, sec, sec], None]


class Sticky(Input):
    """
    An `Offset` offsets the position of the contained Input.
    """

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.meta = Metadata(interface=True)
        return instance

    def __init__(
        self,
        input: Input,
        modifiersAndCallbacks: list[tuple[type[IShader], Callback]],
    ):
        self.input = input
        self.modifiersAndCallbacks = modifiersAndCallbacks

    def flush(self) -> Self:
        self.input.flush()
        return self

    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = 1) -> Self:
        """
        Applies some `Transformations` to the `Input`.

        The `duration` is in `seconds`, so it will affect `duration * framerate` frames of the video.
        """

        allShaders = []

        for s in shaders:
            shader = copy.deepcopy(s)

            for shaderType, callback in self.modifiersAndCallbacks:
                if type(s) == shaderType:
                    callback(self, shader, start, duration)

            allShaders.append(shader)

        self.input.apply(*allShaders, start=start, duration=duration)

        return self

    def __str__(self) -> str:
        return f"\nSticky:\n{self.input}"

    def __repr__(self) -> str:
        return self.__str__()
