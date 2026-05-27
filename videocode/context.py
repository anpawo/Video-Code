#!/usr/bin/env python3


from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Callable
from videocode.constants import *


if TYPE_CHECKING:
    from videocode.shader.ishader import IShader


class Metadata:
    def __init__(self, *, interface: bool = False) -> None:
        # --- Index
        """
        Index of the `Input`.

        Groups do not have an index (they are just python wrapper)
        """
        self.index: int = cast(int, None) if interface else Context.getIndex()

        # --- Position ---
        self.position: v2[wnumber, wnumber] = v2(0, 0)

        # --- Align ---
        self.align: v2[wnumber, wnumber] = v2(0.5, 0.5)

        # --- Scale ---
        self.scale: v2[wnumber, wnumber] = v2(1, 1)

        # --- Rotation ---
        self.rotation: number = 0

        # --- Opacity ---
        self.opacity: number = 255

        # --- Hidden ---
        self.hidden: bool = False

        # --- Offset ---
        self.lastAffectedFrame: frame = Context.waitOffset
        """
        Last frame affected by a `Transformation` from the last applied `Transformation`

        Starts at waitOffset because any waits should consume all previous effects.
        """
        self.transformationOffset: frame = self.lastAffectedFrame
        """
        Increased by `lastAffectedFrame` when flushed.

        Also starts at Global.waitOffset
        """

        # --- Delay ---
        self.pendingStart: sec = 0
        """
        Keep start through setattr.
        """
        self.pendingDuration: sec = SINGLE_FRAME
        """
        Keep duration through setattr.
        """
        self.pendingOffset: maybe[frame] = None
        """
        Keep transformation offset through setattr.
        """

        # --- Callbacks ---
        self.callbacks: dict[type[IShader], list[Callable[[IShader, sec, sec, frame], None]]] = {}

    def __str__(self) -> str:
        s = "\n"
        for k, v in self.__dict__.items():
            s += f"\t\t{k}={v}\n"
        return s


class StackAction:

    @abstractmethod
    def __init__(self): ...

    def __str__(self) -> str:
        return str(vars(self))

    def jsonSerialization(self):
        return vars(self)


class Create(StackAction):
    def __init__(self, inputType: str, inputArgs: dict[str, Any]):
        self.action = self.__class__.__name__
        self.type = inputType
        self.args = inputArgs


class Apply(StackAction):
    def __init__(self, inputIndex: int, shaderName: str, shaderType: str, shaderArgs: dict[str, Any]):
        self.action = self.__class__.__name__
        self.input = inputIndex
        self.name = shaderName
        self.type = shaderType
        self.args = shaderArgs


class Wait(StackAction):
    def __init__(self, numberOfFrame: int):
        self.action = self.__class__.__name__
        self.n = numberOfFrame


class Timestamp(StackAction):
    def __init__(self, name: str, time: int):
        self.action = self.__class__.__name__
        self.name = name
        self.time = time


class Context:
    """
    Context containing the `Metadata` of the `Scene`.
    """

    # Represents the steps to generate the video.
    stack: list[StackAction] = []

    # O(1) deduplication index for Apply actions.
    # Key: (inputIndex, shaderName, shaderType, start, duration, argName)
    # Value: index into stack[] where that Apply lives.
    # Mirrors the dedup criteria in apply() — updated on every append or replace.
    _applyIndex: dict[tuple, int] = {}

    # Index of the next `Input`
    inputCounter: int = 0

    # Last ever affected frame
    lastEverAffectedFrame: frame = 0

    # Wait creates an offset affecting the start of any transformation
    waitOffset: frame = 0

    @staticmethod
    def getIndex() -> int:
        Context.inputCounter += 1
        return Context.inputCounter - 1

    @staticmethod
    def create(inputType: str, inputArgs: dict[str, Any]):
        Context.stack.append(Create(inputType, inputArgs))

    @staticmethod
    def apply(inputIndex: int, shaderName: str, shaderType: str, shaderArgs: dict[str, Any]):
        a = Apply(inputIndex, shaderName, shaderType, shaderArgs)
        # Dedup key mirrors the original three conditions:
        #   sameShader : (inputIndex, shaderName, shaderType)
        #   sameTiming : start, duration
        #   sameArg    : for "Args" shaders also include the arg name; None otherwise
        argName = shaderArgs.get("name") if shaderName == "Args" else None
        key = (inputIndex, shaderName, shaderType,
               shaderArgs.get("start"), shaderArgs.get("duration"), argName)
        idx = Context._applyIndex.get(key)
        if idx is not None:
            Context.stack[idx] = a   # replace in-place, index stays valid
        else:
            Context._applyIndex[key] = len(Context.stack)
            Context.stack.append(a)


def wait(n: sec = 0) -> None:
    """
    Wait for all animations to end and then pauses for `n` frames.

    Can be used to synchronize everything before moving on.
    """
    n = int(n * FRAMERATE)

    # Python
    Context.waitOffset = Context.lastEverAffectedFrame = max(Context.lastEverAffectedFrame, Context.waitOffset) + n

    # Cpp
    Context.stack.append(Wait(n))


def timestamp(name: str) -> None:
    Context.stack.append(Timestamp(name, Context.lastEverAffectedFrame))


# TODO: background level
