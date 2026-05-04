#!/usr/bin/env python3


import copy


from videocode.input.input import *


class Group(Input):
    # fmt: off
    """
    A `Group` contains many inputs and will apply each transformations it gets to all of its inputs.

    Also used to create bigger things that link many Inputs.  
    You create a class that inherits from `Group`, setup your things and then super().__init__().
    """
    # fmt: on

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.meta = Metadata(interface=True)
        return instance

    def __init__(self, *inputs: Input):
        self._inputs = [i for i in inputs]

    def addInput(self, *inputs: Input) -> Self:
        for i in inputs:
            self._inputs.append(i)
        return self

    def flush(self) -> Self:
        """
        Appends the `frames` of `self` to the `timeline`.
        """
        for i in self._inputs:
            i.flush()

        return self

    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = 1) -> Self:
        """
        Applies the `Transformations` `ts` to all the `Inputs` of the `Group`.
        """
        for s in shaders:
            for i in self._inputs:
                i.apply(copy.deepcopy(s), start=start, duration=duration)

        return self

    def waitForOthers(self, n: sec = 0, updateContext=False) -> Self:
        lastAffectedFramePlusN = max(i.meta.lastAffectedFrame for i in self._inputs) + int(n * FRAMERATE)

        for i in self._inputs:
            i.waitTo(lastAffectedFramePlusN)

        if updateContext and lastAffectedFramePlusN >= Context.lastEverAffectedFrame:
            Context.waitOffset = Context.lastEverAffectedFrame = lastAffectedFramePlusN

        return self

    def _broadcast(self, name: str, *args, **kwargs) -> Self:
        for child in self._inputs:
            getattr(child, name)(*args, **kwargs)
        return self

    # fmt: off
    def moveTo(self, *args, **kwargs) -> Self: return self._broadcast('moveTo', *args, **kwargs)
    def moveBy(self, *args, **kwargs) -> Self: return self._broadcast('moveBy', *args, **kwargs)
    def scaleTo(self, *args, **kwargs) -> Self: return self._broadcast('scaleTo', *args, **kwargs)
    def scaleBy(self, *args, **kwargs) -> Self: return self._broadcast('scaleBy', *args, **kwargs)
    def rotateTo(self, *args, **kwargs) -> Self: return self._broadcast('rotateTo', *args, **kwargs)
    def rotateBy(self, *args, **kwargs) -> Self: return self._broadcast('rotateBy', *args, **kwargs)
    def alignTo(self, *args, **kwargs) -> Self: return self._broadcast('alignTo', *args, **kwargs)
    def fadeIn(self, *args, **kwargs) -> Self: return self._broadcast('fadeIn', *args, **kwargs)
    def fadeOut(self, *args, **kwargs) -> Self: return self._broadcast('fadeOut', *args, **kwargs)
    # fmt: on

    def __str__(self) -> str:
        return "".join(f"idx=[{idx}], i=[{type(i).__name__}]]\n" for idx, i in enumerate(self._inputs))

    def __repr__(self) -> str:
        return self.__str__()
