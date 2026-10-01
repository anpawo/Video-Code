#!/usr/bin/env python3

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Callable, Self
from videocode.context import Metadata, frame
from videocode.input.input import Input
from videocode.constants import FRAMERATE
from videocode.ty import sec


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
        if n < 0:
            raise ValueError(f"waitTo({n}) — there is no frame before the first one.")
        self.broadcast(lambda i: i._clockTo(n))
        return self

    def wait(self, n: float) -> Self:
        self.broadcast(lambda i: i.wait(n))
        return self

    def waitFor(self, i: Input | sec) -> Self:
        if isinstance(i, (int, float)):
            until = int(round(i * FRAMERATE))
            self.broadcast(lambda m: m._clockTo(max(until, m.meta.lastAffectedFrame)))
            return self
        frames: list[frame] = []
        i.broadcast(lambda m: frames.append(m.meta.lastAffectedFrame))
        self.broadcast(lambda m: m._clockTo(max(frames)))
        return self
