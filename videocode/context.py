#!/usr/bin/env python3


from typing import TYPE_CHECKING, Any
from videocode.constants import *


if TYPE_CHECKING:
    from videocode.input.input import Input


class Metadata:
    def __init__(self, *, interface: bool = False) -> None:
        # --- Index
        """
        Index of the `Input`.

        Groups do not have an index (they are just python wrapper)
        """
        self.index: maybe[int] = None if interface else Context.getIndex()

        # --- Name of the Parent Input (setup by the Input itself) ---
        self.name: str

        # --- Position ---
        self.position: v2[number] = v2(0, 0)

        # --- Align ---
        self.align: v2[number] = v2(0.5, 0.5)

        # --- Scale ---
        self.scale: v2[number] = v2(1, 1)

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
        self.pendingSetattrStart: defaultable[sec] = default(0)
        """
        Keep start through setattr.
        """
        self.pendingSetattrDuration: defaultable[sec] = default(1)
        """
        Keep duration through setattr.
        """

        # --- Property Attributes ---
        self.props: set[str] = set()

    def __str__(self) -> str:
        s = "\n"
        for k, v in self.__dict__.items():
            s += f"\t\t{k}={v}\n"
        return s


class Context:
    """
    Context containing the `Metadata` of the `Scene`.
    """

    # Represents the steps to generate the video.
    stack: list[dict[str, Any]] = []

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

    def __str__(self) -> str:
        return f"Stack={self.stack}"

    def __repr__(self) -> str:
        return str(self)


def wait(n: sec = 0) -> None:
    """
    Wait for all animations to end and then pauses for `n` frames.

    Can be used to synchronize everything before moving on.
    """
    n = int(n * FRAMERATE)

    # Python
    Context.waitOffset = Context.lastEverAffectedFrame + n

    # Cpp
    Context.stack.append(
        {
            "action": "Wait",
            "n": n,
        },
    )


def timestamp(name: str) -> None:
    Context.stack.append(
        {
            "action": "Timestamp",
            "name": name,
            "time": Context.waitOffset,
        }
    )
