#!/usr/bin/env python3


from videocode.input.Input import *
from videocode.transformation.setter.SetPosition import setPosition


class group(Input):
    """
    A `Group` contains many inputs and will apply each transformations it gets to all of its inputs.
    """

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.index = None
        instance.meta = Global.getDefaultMetadata()
        return instance

    def __init__(self, *inputs: Input | tuple[position, Input]):
        self.inputs: list[Input] = [i[1] if isinstance(i, tuple) else i for i in inputs]
        self.modifiers: list[position] = [i[0] if isinstance(i, tuple) else (0, 0) for i in inputs]

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
        for idx, i in enumerate(self.inputs):
            for t in ts:
                t.modificator(self.meta)

                # Relative Position
                if type(t) == setPosition:
                    __t = copy.deepcopy(t)
                    if __t.x:
                        __t.x += self.modifiers[idx][0]
                    if __t.y:
                        __t.y += self.modifiers[idx][1]

                    __t.modificator(i.meta)

                    i.apply(copy.deepcopy(__t), start=start, duration=duration)
                else:
                    t.modificator(i.meta)

                    i.apply(copy.deepcopy(t), start=start, duration=duration)

        if hasattr(self.meta, 'automaticAdder') and self.meta.automaticAdder:
            self.add()

        return self

    def __str__(self) -> str:
        return "".join(f"idx=[{idx}], i=[{type(i).__name__}, pos=[{self.modifiers[idx]}]]\n" for idx, i in enumerate(self.inputs))

    def __repr__(self) -> str:
        return self.__str__()
