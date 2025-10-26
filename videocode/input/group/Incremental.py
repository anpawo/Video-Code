#!/usr/bin/env python3


from types import UnionType
from typing import Any, Callable
from videocode.input.Input import *
from videocode.input.group.Group import group


class incremental(group):
    """
    An `Incremental` is a `Group` that modify the transformations it receives before applying them to each of its `Input`.

    Usually the modification is an incrementation according to the index of the input (hence the name).
    """

    def __init__(self, incrementals: dict[type, tuple[Callable[[Transformation, Index], Transformation], ...]], *inputs: Input):
        group.__init__(self, *inputs)
        self.incrementals = incrementals

    def apply(self, *ts: Transformation, start: t = default(0), duration: t = default(1)) -> Self:
        for i, input in enumerate(self.inputs):
            for t in ts:
                t.modificator(self.meta)

                if type(t) in self.incrementals:
                    __t = copy.deepcopy(t)
                    for incr in self.incrementals[type(t)]:
                        __t = incr(__t, i)
                    input.apply(__t, start=start, duration=duration)
                else:
                    input.apply(copy.deepcopy(t), start=start, duration=duration)

        return self


# --- Incremental Functions ---


def linearAdd(**kwargs) -> Callable[[Transformation, Index], Transformation]:

    def wrapper(t: Transformation, i: Index) -> Transformation:
        for k, v in kwargs.items():
            t.__setattr__(k, t.__getattribute__(k) + v * i)
        return t

    return wrapper


def constantAdd(**kwargs) -> Callable[[Transformation, Index | None], Transformation]:

    def wrapper(t: Transformation, _: Index | None = None) -> Transformation:
        for k, v in kwargs.items():
            t.__setattr__(k, t.__getattribute__(k) + v)
        return t

    return wrapper
