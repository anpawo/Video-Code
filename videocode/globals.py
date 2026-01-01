#!/usr/bin/env python3


from typing import Any
from videocode.constants import *


class Metadata:
    def __init__(self, d: dict, *, interface: bool = False) -> None:
        # --- Index
        """
        Index of the `Input`.

        Groups do not have an index (they are just python wrapper)
        """
        self.index: maybe[int] = None if interface else Global.getIndex()

        # --- Position ---
        self.position: v2[number] = v2(0, 0)

        # --- Align ---
        self.align: v2[number] = v2(0.5, 0.5)

        # --- Scale ---
        self.scale: v2[number] = v2(1, 1)

        # --- Rotation ---
        self.rotation: number = 0

        # --- Hidden ---
        self.hidden: bool = False

        # --- Args ---
        self.args: dict = d

        # --- Offset ---
        self.lastAffectedFrame: int = 0
        """
        Last frame affected by a `Transformation` from the last applied `Transformation`
        """
        self.transformationOffset: int = 0
        """
        Increased by `lastAffectedFrame` when flushed.
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

    # Wait creates an offset affecting the start of any transformation
    waitOffset: int = 0

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
    Global.waitOffset += int(n * FRAMERATE)
