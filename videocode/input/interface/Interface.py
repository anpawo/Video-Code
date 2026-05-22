#!/usr/bin/env python3


from abc import abstractmethod
from typing import Any, Callable, Self
from videocode.context import Metadata, frame
from videocode.input.input import Input
from videocode.constants import FRAMERATE


class Interface(Input):

    def __new__(cls, *args, **kwargs) -> Self:
        instance = object.__new__(cls)
        instance.meta = Metadata(interface=True)
        return instance

    @abstractmethod
    def broadcast(self, func: Callable[[Input], Any]): ...

    def flush(self) -> Self:
        self.broadcast(lambda i: i.flush())
        return self

    def waitTo(self, n: frame) -> Self:
        self.broadcast(lambda i: i.waitTo(n))
        return self

    def wait(self, n: float) -> Self:
        self.broadcast(lambda i: i.wait(n))
        return self

    def waitFor(self, other: Input) -> Self:
        self.broadcast(lambda i: i.waitTo(other.meta.lastAffectedFrame))
        return self
