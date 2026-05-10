#!/usr/bin/env python3


from typing import Any


from videocode.input.input import *
from videocode.input.interface.Interface import Interface


class Group(Interface):
    # fmt: off
    """
    A `Group` contains many inputs and will apply each transformations it gets to all of its inputs.

    Also used to create bigger things that link many Inputs.  
    You create a class that inherits from `Group`, setup your things and then super().__init__().
    """
    # fmt: on

    def __init__(self, *inputs: Input):
        self._inputs = [i for i in inputs]

    def __getattribute__(self, name: str) -> Any:
        """
        Broacast non-local methods to all children.
        """
        methods = {
            "__setattr__",
            "__delattr__",
        }

        youngestChild: type = object.__getattribute__(self, "__class__")
        mro = youngestChild.__mro__
        groupIndex = mro.index(Group)

        for cls in mro[: groupIndex + 1]:  # Skip Below Group
            currDict = cls.__dict__
            methods.update(k for k in currDict if callable(currDict[k]))

        # Child & Self Methods
        if name in methods:
            return super().__getattribute__(name)

        # Attribute Name
        attr = super().__getattribute__(name)

        # Is Attribute
        if not callable(attr):
            return attr

        # Any Other Method (From Input)
        def broadcastWrapper(*args, **kwargs):
            children = self._inputs

            for child in children:
                getattr(child, name)(*args, **kwargs)

            return self

        # Wrapper Will Be Called Instantly (Most Likely)
        return broadcastWrapper

    def addInput(self, *inputs: Input) -> Self:
        for i in inputs:
            self._inputs.append(i)
        return self

    # TODO: needs a fix
    # def waitForOthers(self, n: sec = 0) -> Self:
    #     transformationOffsetPlusN = max(i.meta.transformationOffset for i in self._inputs) + int(n * FRAMERATE)

    #     for i in self._inputs:
    #         i.waitTo(transformationOffsetPlusN)

    #     return self
