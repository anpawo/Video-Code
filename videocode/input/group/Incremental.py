#!/usr/bin/env python3


from typing import Callable
from videocode.input.Input import *
from videocode.input.group.Group import group


class incremental(group):
    def __init__(self, incrementals: dict[type, Callable[[Transformation, Index], Transformation]], *inputs: Input):
        group.__init__(self, *inputs)
        self.incrementals = incrementals

    def apply(self, *ts: Transformation, start: sec = default(0), duration: sec = default(1)) -> Self:  # type: ignore
        """
        Applies the `Transformations` `ts` to all the `Inputs` of the `Group`.

        The duration is in seconds, so it will affect `duration * framerate` frames of the video.
        """
        for i, input in enumerate(self.inputs):
            for t in ts:
                if type(t) in self.incrementals:
                    input.apply(self.incrementals[type(t)](copy.deepcopy(t), i), start=start, duration=duration)
                else:
                    input.apply(copy.deepcopy(t), start=start, duration=duration)

        if self.meta.automaticAdder:
            return self.add()
        else:
            return self


def linearAdd(**kwargs) -> Callable[[Transformation, Index], Transformation]:

    def wrapper(t: Transformation, i: Index) -> Transformation:
        for k, v in kwargs.items():
            t.__setattr__(k, t.__getattribute__(k) + v * i)

        return t

    return wrapper
