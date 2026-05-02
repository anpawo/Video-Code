#!/usr/bin/env python3


import copy


from videocode.input.input import *
from videocode.input.offset.Offset import Offset
from videocode.shader.vertexShader.position import position


class Group(Input):
    """
    A `Group` contains many inputs and will apply each transformations it gets to all of its inputs.
    """

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.meta = Metadata(interface=True)
        return instance

    def __init__(self, *inputs: Input):
        self.inputs = [i for i in inputs]

    def addInput(self, *inputs: Input) -> Self:
        for i in inputs:
            self.inputs.append(i)
        return self

    def flush(self) -> Self:
        """
        Appends the `frames` of `self` to the `timeline`.
        """
        for i in self.inputs:
            i.flush()

        return self

    def apply(self, *shaders: IShader, start: defaultable[sec] = default(0), duration: defaultable[sec] = default(1)) -> Self:
        """
        Applies the `Transformations` `ts` to all the `Inputs` of the `Group`.
        """
        for s in shaders:
            for i in self.inputs:
                i.apply(copy.deepcopy(s), start=start, duration=duration)

        return self

    def waitForOthers(self, n: sec = 0, updateContext=False) -> Self:
        lastAffectedFramePlusN = max(i.meta.lastAffectedFrame for i in self.inputs) + int(n * FRAMERATE)

        for i in self.inputs:
            i.waitTo(lastAffectedFramePlusN)

        if updateContext and lastAffectedFramePlusN >= Context.lastEverAffectedFrame:
            Context.waitOffset = Context.lastEverAffectedFrame = lastAffectedFramePlusN

        return self

    def __str__(self) -> str:
        return "".join(f"idx=[{idx}], i=[{type(i).__name__}]]\n" for idx, i in enumerate(self.inputs))

    def __repr__(self) -> str:
        return self.__str__()
