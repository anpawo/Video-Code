#!/usr/bin/env python3


from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Callable
from videocode.constants import *


if TYPE_CHECKING:
    from videocode.shader.ishader import IShader
    from videocode.input.input import Input


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

        # --- ZIndex ---
        # Defaults to creation order (no ties unless explicitly set).
        self.zIndex: int = self.index if self.index is not None else 0

        # Bumped via Context.nextZOrderSeq() every time zIndex is explicitly
        # set. Ties in zIndex are broken by this: the most recently changed
        # one wins (renders on top), regardless of creation order.
        self.zOrderSeq: int = 0

        if not interface:
            Context.metas.append(self)

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
        self.preCallbacks: dict[type[IShader], list[Callable[[IShader, sec, sec, frame], bool]]] = {}
        self.postCallbacks: dict[type[IShader], list[Callable[[IShader, sec, sec, frame], None]]] = {}

        # --- Mirroring ---
        self.mirrorTargets: list[Input] = []
        """
        Inputs that should receive a copy of every shader applied to this one
        (see `Input.mirror`). Each target resolves the replicated shader
        against its own state — directional, self -> targets.
        """

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


class Wait(StackAction):
    def __init__(self, startFrame: int, numberOfFrame: int):
        self.action = self.__class__.__name__
        self.start = startFrame
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

    # stack[inputIdx][-1]            = {"type": str, "args": dict}          — Create
    # stack[inputIdx][frameIdx][key] = {"type": shaderType, **shaderArgs}   — Apply
    # "Args" shaders use key "Args:{argName}" to allow multiple per frame.
    stack: dict[int, dict] = {}

    # Wait and Timestamp actions; C++ consumes these separately.
    events: list[StackAction] = []

    # Index of the next `Input`
    inputCounter: int = 0

    # Last ever affected frame
    lastEverAffectedFrame: frame = 0

    # Wait creates an offset affecting the start of any transformation
    waitOffset: frame = 0

    # Monotonic counter for zIndex tiebreaks — see Metadata.zOrderSeq
    zOrderCounter: int = 0

    # Every non-interface Metadata ever created — used to resolve relative
    # layer-order operations (bringToFront, sendToBack, bringForward, sendBackward).
    metas: list[Metadata] = []

    @staticmethod
    def getIndex() -> int:
        Context.inputCounter += 1
        return Context.inputCounter - 1

    @staticmethod
    def nextZOrderSeq() -> int:
        Context.zOrderCounter += 1
        return Context.zOrderCounter

    @staticmethod
    def maxZIndex() -> int:
        return max((m.zIndex for m in Context.metas if m.zIndex != BACKGROUND_Z_INDEX), default=0)

    @staticmethod
    def minZIndex() -> int:
        return min((m.zIndex for m in Context.metas if m.zIndex != BACKGROUND_Z_INDEX), default=0)

    @staticmethod
    def zIndexAbove(z: int) -> maybe[int]:
        """Smallest zIndex among all non-background inputs strictly greater than `z`, or None."""
        candidates = [m.zIndex for m in Context.metas if m.zIndex != BACKGROUND_Z_INDEX and m.zIndex > z]
        return min(candidates) if candidates else None

    @staticmethod
    def zIndexBelow(z: int) -> maybe[int]:
        """Largest zIndex among all non-background inputs strictly less than `z`, or None."""
        candidates = [m.zIndex for m in Context.metas if m.zIndex != BACKGROUND_Z_INDEX and m.zIndex < z]
        return max(candidates) if candidates else None

    @staticmethod
    def create(inputIndex: int, inputType: str, inputArgs: dict[str, Any]):
        Context.stack.setdefault(inputIndex, {})[-1] = {"type": inputType, "args": inputArgs}

    @staticmethod
    def apply(inputIndex: int, shaderName: str, shaderType: str, shaderArgs: dict[str, Any]):
        frameIdx = shaderArgs["start"]
        argName = shaderArgs.get("name") if shaderName == "Args" else None
        dictKey = f"Args:{argName}" if argName is not None else shaderName
        Context.stack.setdefault(inputIndex, {}).setdefault(frameIdx, {})[dictKey] = {
            "type": shaderType,
            "args": shaderArgs,
        }


def wait(n: sec = 0) -> None:
    """
    Wait for all animations to end and then pauses for `n` frames.

    Can be used to synchronize everything before moving on.
    """
    n = int(n * FRAMERATE)

    # Python
    startFrame = max(Context.lastEverAffectedFrame, Context.waitOffset)
    Context.waitOffset = Context.lastEverAffectedFrame = startFrame + n

    Context.events.append(Wait(startFrame, n))


def timestamp(name: str) -> None:
    Context.events.append(Timestamp(name, Context.lastEverAffectedFrame))
