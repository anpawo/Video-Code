#!/usr/bin/env python3


from videocode.input.Input import *


class group(Input):
    def __init__(self, *inputs: Input):
        self.inputs: list[Input] = [*inputs]

    def add(self) -> Self:
        """
        Appends the `frames` of `self` to the `timeline`.
        """
        Global.stack.append(
            {
                "action": "Add",
                "input": [i.index for i in self.inputs],
            }
        )
        return self

    def apply(self, *ts: Transformation, start: sec = default(0), duration: sec = default(1)) -> Input:  # type: ignore
        """
        Applies the `Transformations` `ts` to all the `Inputs` of the `Group`.

        The duration is in seconds, so it will affect `duration * framerate` frames of the video.
        """
        for i in self.inputs:
            for t in ts:
                i.apply(copy.deepcopy(t), start=start, duration=duration)
        return self
