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
    """
    A callable that takes an Input and yields IShader instances.

    Applied to a `Group`, it runs once PER MEMBER, so each call sees that
    member's own state — that is what lets `typewriter` stagger letter by
    letter and `highlight` flash each letter's own colour. An effect that
    only means something across the whole group is a `GroupEffect`.
    """

    def __call__(self, input: Input, /) -> Generator[IShader, Any, None]: ...


class GroupEffect:
    """
    An `Effect` that only means something across a whole `Group`, so it
    receives the GROUP itself instead of being dispatched to its members —
    `fillIn` sweeps ONE boundary over a word, not one wipe per letter.

    Two things make an effect group-scoped: it sweeps across its target (a
    letter cannot know it is the 7th of 12, nor where the word starts), or it
    ASSIGNS an attribute rather than yielding shaders, because assignment is
    what routes a value through a group's own distribution — `Text.fillColor`
    slices a gradient per letter, and only the Text can do that.

        def fillIn(...) -> GroupEffect:
            def _apply(input: Input) -> Generator[IShader, Any, None]: ...
            return GroupEffect(_apply)

    On a plain `Input` nothing differs: a leaf has no members to split for.
    """

    def __init__(self, apply: Effect) -> None:
        self._apply = apply

    def __call__(self, input: Input, /) -> Generator[IShader, Any, None]:
        return self._apply(input)


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


class Paint:
    """
    A fill that GENERATES its pixels from position and time, ignoring what is
    underneath — only the shape's coverage is kept. silk, fire, starNest,
    evilEye, any mathShader.

    A paint is a VALUE, not a shader, and that is the whole of its design.
    `fillColor=fire()` goes exactly where a colour goes: it rides
    `args["fillColor"]`, it is serialised beside `rgba` and `LinearGradient`,
    and it persists until something reassigns it. The C++ reads it as per-frame
    state and injects it into the effect chain on every frame it is active
    (`AInput::getActiveEffectsAtFrame`).

    It used to inherit `IShader`, and that was a lie the type system told:
    a paint uses NOTHING `IShader` provides. `start`, `duration` and `offset`
    were always None, `_rigidKind` always 0, and the one thing an `IShader`
    exists for — being `.apply()`d — is the one thing a paint is explicitly
    forbidden to do. The inheritance also handed the author an API that does
    not work: `silk().at(start=2)` type-checked, stored the values, and then
    dropped them at serialisation. No error, no effect.

    Timing a paint is timing the ASSIGNMENT, which is what `over()` already
    does and what a colour does too:

        rect.over(duration=0.6).fillColor = silk()

    Adding a new paint needs no new machinery: a `.glsl` in assets/mathshaders
    and a function returning `mathShader(filepath=...)`. Only a preset with its
    own uniform needs a subclass, and only that case needs `generator`.
    """

    # The name the C++ factory knows this paint by, when it is not this class's
    # own name. A preset that subclasses one to add uniforms (evilEye) is still
    # that paint on the C++ side — the factory binds the base, not the preset.
    generator: maybe[str] = None

    def jsonSerialization(self) -> dict:
        # {"shader": <generator>, <its args>}. The C++ discriminates the fill
        # slot on the PRESENCE of the "shader" key — a solid colour is a number,
        # a gradient is a list, a paint is an object with this key — so the wire
        # format is already the three-way union this class now matches. Numeric
        # args reach the GLSL alphabetically (the usual p[] contract) and
        # "filepath" rides ActiveEffect::strParam.
        return {"shader": self.generator or upperFirst(type(self).__name__)} | dict(vars(self))


    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


# The old name, kept so nothing outside has to change at once. A paint was
# never a shader; it is spelled that way in scenes written before this.
PaintShader = Paint


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
