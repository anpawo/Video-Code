#!/usr/bin/env python3


from videocode.input.Input import *
from videocode.input.group.Group import group


class incrementalGroup(group):
    def __init__(self, *inputs: Input):
        super().__init__(*inputs)

    def apply(self, *ts: Transformation, start: sec = default(0), duration: sec = default(1)) -> Self:  # type: ignore
        """
        Applies the `Transformations` `ts` to all the `Inputs` of the `Group`.

        The duration is in seconds, so it will affect `duration * framerate` frames of the video.
        """
        for input in self.inputs:
            for i, t in enumerate(ts):
                input.apply(copy.deepcopy(t), start=start, duration=duration)

        if self.meta.automaticAdder:
            return self.add()
        else:
            return self
