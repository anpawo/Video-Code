#!/usr/bin/env python3


from typing import Any, TypeVar
from videocode.input.input import *
from videocode.input.interface.Interface import Interface


_GROUP_T = TypeVar("_GROUP_T", bound=Input, default=Input)


class Group(Interface, Generic[_GROUP_T]):
    # fmt: off
    """
    A `Group` contains many inputs and will apply each transformations it gets to all of its inputs.

    Also used to create bigger things that link many Inputs.  
    You create a class that inherits from `Group`, setup your things and then super().__init__().
    """
    # fmt: on

    def __init__(self, *inputs: Input):
        self.inputs: list[_GROUP_T] = cast(list[_GROUP_T], [i for i in inputs])

    def broadcast(self, func: Callable[[Input], Any]):
        for child in self.inputs:
            func(child)

    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        for s in shaders:
            for i in self.inputs:
                # Transformations affect the Group's Metadata
                if isinstance(s, VertexShader):
                    deepcopy(s).modify(self)

                # Transformations affect the Input's Metadata
                i.apply(deepcopy(s), start=start, duration=duration, offset=offset)
        return self

    def waitForOthers(self) -> Self:
        frames: list[int] = []

        def collect(i: Input) -> None:
            if isinstance(i, Interface):
                i.broadcast(collect)
            else:
                frames.append(i.meta.lastAffectedFrame)

        self.broadcast(collect)
        if len(frames) == 0:
            return self
        return self.waitTo(max(frames))

    def __str__(self) -> str:
        s = f"{self.__class__.__name__}"
        return s

    def __repr__(self) -> str:
        return self.__str__()
