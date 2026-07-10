#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator, Protocol, Self, runtime_checkable
from videocode.constants import *
from videocode.utils.funcutils import *

if TYPE_CHECKING:
    from videocode.input.input import Input


@runtime_checkable
class Effect(Protocol):
    """A callable that takes an Input and yields IShader instances."""
    def __call__(self, input: Input, /) -> Generator[IShader, Any, None]: ...


class IShader(ABC):
    """
    A `Effect` modifies an input.
    """

    _type: str
    _rigidKind: int = 0  # 0=none, 1=position, 2=rotation, 3=scale (set by subclasses)

    start: maybe[sec] = None
    duration: maybe[sec] = None
    offset: maybe[frame] = None

    def at(self, *, start: sec, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        self.start = start
        self.duration = duration
        self.offset = offset
        return self

    def resolve(self, start: sec, duration: sec, offset: maybe[frame]) -> tuple[sec, sec, maybe[frame]]:
        """
        Use self default values if any else given ones.
        """
        return (
            self.start if self.start is not None else start,
            self.duration if self.duration is not None else duration,
            self.offset if self.offset is not None else offset,
        )

    @abstractmethod
    def __init__(self) -> None: ...

    def __copy__(self) -> Self:
        # Faster than the default copy.copy(): skips the generic
        # __reduce_ex__/copyreg machinery for these plain-attribute objects.
        new = self.__class__.__new__(self.__class__)
        vars(new).update(vars(self))
        return new

    def __str__(self) -> str:
        s = f"{self.__class__.__name__}"
        return s

    def __repr__(self) -> str:
        return self.__str__()


class FragmentShader(IShader):
    """
    A `FragmentShader` FILTERS the pixels of an `Input` — it transforms what
    is already there: blur, grayscale, glow, lut, chromaKey... Used via
    `.apply()`. (Shaders that GENERATE pixels are their own kind — see
    `PaintShader`.)
    """

    _type = "FragmentShader"


class PaintShader(IShader):
    """
    The third shader kind, independent of the other two: a `PaintShader`
    GENERATES pixels from position and time, ignoring what's underneath
    (only the shape's coverage is kept) — silk, fire, starNest, any
    mathShader.

    A paint is FILL STATE, nothing else: `fillColor=fire()` rides
    `args["fillColor"]` exactly like a color (via `jsonSerialization`, like
    gradients do) and persists until reassigned — the C++ injects it into
    the effect chain on every frame it is active
    (`AInput::getActiveEffectsAtFrame`). It can NOT be `.apply()`d
    (`Input.apply` rejects it), and the `paint` alias (`rgba | PaintShader`)
    can never admit a `FragmentShader` — the three shader kinds don't
    overlap.
    """

    def jsonSerialization(self) -> dict:
        # {"shader": <effect name>, <its args>} — the "shader" key is what the
        # C++ fillColor parsing/injection discriminates on; numeric args reach
        # the GLSL alphabetically (the usual p[] contract), "filepath" rides
        # ActiveEffect::strParam.
        return {"shader": upperFirst(type(self).__name__)} | {
            k: v for k, v in vars(self).items() if k not in ("start", "duration", "offset")
        }


class VertexShader(IShader):
    """
    A `VertexShader` modifies the metadata of an `Input`.

    ### Geometry
    - position
    - align
    - rotate
    - scale

    ### Visibility
    - opacity
    - hide
    - show

    ### Default arguments of an Input
    - args
    """

    _type = "VertexShader"

    def autodestroy(self, i: Input) -> bool:
        return False

    @abstractmethod
    def modify(self, i: Input) -> None:
        """
        Modify the `Input`'s `Metadata`. (may do more)

        We want the python interface to keep trace of the changes made on the inputs but they need
        to be applied the moment the transformations are applied, not the moment they are created.
        """
