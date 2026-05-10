#!/usr/bin/env python3


from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Callable
from videocode.constants import *
from videocode.utils.funcutils import upperFirst


if TYPE_CHECKING:
    from videocode.input.input import Input
    from videocode.shader.ishader import VertexShader, IShader


class Metadata:
    def __init__(self, *, interface: bool = False) -> None:
        # --- Index
        """
        Index of the `Input`.

        Groups do not have an index (they are just python wrapper)
        """
        self.index: int = -1 if interface else Context.getIndex()

        # --- Position ---
        self.position: v2 = v2(0, 0)

        # --- Align ---
        self.align: v2 = v2(0.5, 0.5)

        # --- Rotation ---
        self.rotation: number = 0

        # --- Scale ---
        self.scale: v2 = v2(1, 1)

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
        self.transformationOffset: int = self.lastAffectedFrame
        """
        Increased by `lastAffectedFrame` when flushed.

        Also starts at Global.waitOffset
        """

        # --- SetAttr On ---
        self.setattrCallbackOn = False
        """
        Setting an Attribute will trigger an `apply(args(attr))`
        """
        self.pendingSetattrStart: sec = 0
        """
        Keep start through setattr.
        """
        self.pendingSetattrDuration: sec = 1
        """
        Keep duration through setattr.
        """

        # --- Callbacks ---
        self.callbacks: dict[type[IShader], list[Callable[[IShader, sec, sec], None]]] = {}

        # --- Property Attributes ---
        self.props: set[str] = set()

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
        Context.stack.append(Apply(inputIndex, shaderName, shaderType, shaderArgs))


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
