#!/usr/bin/env python3


from typing import Any
from videocode.constants import *


class Metadata:
    def __init__(self, *, interface: bool = False) -> None:
        # --- Index
        """
        Index of the `Input`.

        Groups do not have an index (they are just python wrapper)
        """
        self.index: maybe[int] = None if interface else Global.getIndex()

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
        self.lastAffectedFrame: frame = Global.waitOffset
        """
        Last frame affected by a `Transformation` from the last applied `Transformation`

        Starts at waitOffset because any waits should consume all previous effects.
        """
        self.transformationOffset: int = self.lastAffectedFrame
        """
        Increased by `lastAffectedFrame` when flushed.

        Also starts at Global.waitOffset
        """

    def __str__(self) -> str:
        s = "\n"
        for k, v in self.__dict__.items():
            s += f"\t\t{k}={v}\n"
        return s


class Global:
    """
    Global variable containing the `Metadata` of the `Scene`.
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
        Global.inputCounter += 1
        return Global.inputCounter - 1

    def __str__(self) -> str:
        return f"Stack={self.stack}"

    def __repr__(self) -> str:
        return str(self)


# Kind of act like a waitFor(Input)
def wait(n: sec = 0) -> None:
    n = int(n * FRAMERATE)

    # Python
    Global.waitOffset = Global.lastEverAffectedFrame + n

    # Cpp
    Global.stack.append(
        {
            "action": "Wait",
            "n": n,
        },
    )
