#!/usr/bin/env python3


from videocode.input.Input import *
from videocode.transformation.transformation.Position import position


class group(Input):
    """
    A `Group` contains many inputs and will apply each transformations it gets to all of its inputs.
    """

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.index = None
        instance.meta = Metadata(instance.__dict__)
        return instance

    def __init__(self, *inputs: Input | tuple[tuple[number, number], Input]):
        self.inputs: list[Input] = [i[1] if isinstance(i, tuple) else i for i in inputs]
        self.offset: list[tuple[number, number]] = [i[0] if isinstance(i, tuple) else (0, 0) for i in inputs]

    def flush(self) -> Self:
        """
        Appends the `frames` of `self` to the `timeline`.
        """
        for i in self.inputs:
            i.flush()

        return self

    def apply(self, *ts: Effect, start: t = default(0), duration: t = default(1)) -> Self:
        """
        Applies the `Transformations` `ts` to all the `Inputs` of the `Group`.

        The duration is in seconds, so it will affect `duration * framerate` frames of the video.
        """
        for idx, i in enumerate(self.inputs):
            for t in ts:
                # Offset Position
                if type(t) == position:
                    pos = copy.deepcopy(t)
                    if pos.x:
                        pos.x += self.offset[idx][0]
                    if pos.y:
                        pos.y += self.offset[idx][1]

                    i.apply(pos, start=start, duration=duration)
                else:
                    i.apply(t, start=start, duration=duration)

        return self

    def __str__(self) -> str:
        return "".join(f"idx=[{idx}], i=[{type(i).__name__}, pos=[{self.offset[idx]}]]\n" for idx, i in enumerate(self.inputs))

    def __repr__(self) -> str:
        return self.__str__()
