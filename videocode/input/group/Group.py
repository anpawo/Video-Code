#!/usr/bin/env python3


import copy


from videocode.input.Input import *
from videocode.shader.vertexShader.position import position


class group(Input):
    """
    A `Group` contains many inputs and will apply each transformations it gets to all of its inputs.
    """

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.meta = Metadata(instance.__dict__, interface=True)
        return instance

    def __init__(self, *inputs: Input | tuple[tuple[number, number], Input] | tuple[v2[number], Input]):
        self.inputs: list[Input] = [i[1] if isinstance(i, tuple) else i for i in inputs]
        self.offset: list[v2[number]] = [i if isinstance(i, v2) else v2(*i[0]) if isinstance(i, tuple) else v2(0, 0) for i in inputs]

    def flush(self) -> Self:
        """
        Appends the `frames` of `self` to the `timeline`.
        """
        for i in self.inputs:
            i.flush()

        return self

    def apply(self, *ts: Effect, start: defaultable[sec] = default(0), duration: defaultable[sec] = default(1)) -> Self:
        """
        Applies the `Transformations` `ts` to all the `Inputs` of the `Group`.
        """
        for baseT in ts:
            if isinstance(t := copy.deepcopy(baseT), Transformation):
                t.modificator(self.meta)

            for i, offset in zip(self.inputs, self.offset):
                # Prevent modificator fron changing the base
                t = copy.deepcopy(baseT)

                # Offset Position
                if type(t) == position:
                    if t.x is None:
                        t.x = i.meta.position.x
                    if t.y is None:
                        t.y = i.meta.position.y

                    t.x += offset.x
                    t.y += offset.y

                    i.apply(t, start=start, duration=duration)
                else:
                    i.apply(t, start=start, duration=duration)

        return self

    def __str__(self) -> str:
        return "".join(f"idx=[{idx}], i=[{type(i).__name__}, pos=[{self.offset[idx]}]]\n" for idx, i in enumerate(self.inputs))

    def __repr__(self) -> str:
        return self.__str__()
