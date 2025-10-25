#!/usr/bin/env python3


from videocode.input.Input import *


class group(Input):
    """
    A `Group` contains many inputs and will apply each transformations it gets to all of its inputs.
    """

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.index = None
        instance.meta = Global.getDefaultMetadata()
        return instance

    def __init__(self, *inputs: Input):
        self.inputs: list[Input] = [*inputs]

    def add(self) -> Self:
        """
        Appends the `frames` of `self` to the `timeline`.
        """
        for i in self.inputs:
            i.add()

        return self

    def apply(self, *ts: Transformation, start: t = default(0), duration: t = default(1)) -> Self:
        """
        Applies the `Transformations` `ts` to all the `Inputs` of the `Group`.

        The duration is in seconds, so it will affect `duration * framerate` frames of the video.
        """
        for i in self.inputs:
            for t in ts:
                t.modificator(self.meta)

                i.apply(copy.deepcopy(t), start=start, duration=duration)

        if self.meta.automaticAdder:
            return self.add()
        else:
            return self
