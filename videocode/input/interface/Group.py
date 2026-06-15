#!/usr/bin/env python3

from __future__ import annotations

from copy import copy as _shallow_copy
from typing import Any
from typing_extensions import TypeVar
from videocode.input.input import *
from videocode.input.interface.Interface import Interface
from videocode.template.effect.moveTo import groupMoveBy, groupMoveTo


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
            child.broadcast(func)

    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None, _mirrorAncestors: maybe[frozenset[Input]] = None) -> Self:
        ancestors = _mirrorAncestors if _mirrorAncestors is not None else frozenset((self,))

        for s in shaders:
            # Keep group.meta current even though groups never push to C++.
            # Subclasses and external code read group.meta.* directly —
            # e.g. Text.alignLetters reads self.meta.align.x, or user code
            # inspects text.meta.scale to query the group's current logical state.
            # Groups are otherwise stateless — children own the rendering state.
            if isinstance(s, VertexShader):
                _shallow_copy(s).modify(self)

            # Broadcast to each child.  i.apply() makes its own shallow copy for
            # VertexShaders before calling modify(), so passing s directly is safe.
            for i in self.inputs:
                i.apply(s, start=start, duration=duration, offset=offset)

            # Mirror: see Input.apply — replicate to linked targets, cycle-safe.
            for target in self.meta.mirrorTargets:
                if target not in ancestors:
                    target.apply(s, start=start, duration=duration, offset=offset, _mirrorAncestors=ancestors | {target})
        return self

    def moveTo(self, x: maybe[number] = None, y: maybe[number] = None, easing: easing = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(*groupMoveTo(self, x=x, y=y, easing=easing, start=start, duration=duration))

    def moveBy(self, x: maybe[number] = None, y: maybe[number] = None, easing: easing = Easing.InOut, start: sec = 0, duration: sec = 0.4) -> Self:
        return self.apply(*groupMoveBy(x=x, y=y, easing=easing, start=start, duration=duration))

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
