#!/usr/bin/env python3


import copy


from videocode.input.input import *
from videocode.shader.vertexShader.position import position


class Offset[T: Input](Input):
    """
    An `Offset` offsets the position of the contained Input.
    """

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.meta = Metadata(interface=True)
        return instance

    def __init__(self, x: wfloat, y: wfloat, input: T):
        self.inputPosition = v2(*input.meta.position)
        self.input: T = input
        self.inputOffset = v2(x, y)

    @property
    def x(self):
        return self.inputOffset.x

    @property
    def y(self):
        return self.inputOffset.y

    @x.setter
    def x(self, value: wnumber):
        # Setter
        self.inputOffset.x = value

        # Shenanigans
        self.input.apply(position(x=self.inputPosition.x + self.inputOffset.x))

    @y.setter
    def y(self, value: wnumber):
        # Setter
        self.inputOffset.y = value

        # Shenanigans
        self.input.apply(position(y=self.inputPosition.y + self.inputOffset.y))

    def flush(self) -> Self:
        self.input.flush()
        return self

    def apply(self, *shaders: IShader, start: defaultable[sec] = default(0), duration: defaultable[sec] = default(1)) -> Self:
        """
        Applies some `Transformations` to the `Input`.

        The `duration` is in `seconds`, so it will affect `duration * framerate` frames of the video.
        """

        def offsetPosition(s: IShader) -> IShader:
            if type(s) == position:
                s = copy.deepcopy(s)

                if s.x is None:
                    s.x = self.inputPosition.x
                else:
                    self.inputPosition.x = s.x
                if s.y is None:
                    s.y = self.inputPosition.y
                else:
                    self.inputPosition.y = s.y

                s.x += self.inputOffset.x
                s.y += self.inputOffset.y

            return s

        self.input.apply(*map(offsetPosition, shaders), start=start, duration=duration)

        return self

    def __str__(self) -> str:
        return f"\nOffset p({self.inputPosition}), o({self.inputOffset}):\n({self.input})"

    def __repr__(self) -> str:
        return self.__str__()
