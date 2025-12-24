#!/usr/bin/env python3


import copy
from typing import Any
from videocode.Constant import *


class Metadata:
    def __init__(self, d: dict) -> None:
        # --- Position ---
        self.position: v2[number] = v2(*CENTER)

        # --- Align ---
        self.align: v2[number] = v2(-0.5, -0.5)

        # --- Scale ---
        self.scale: v2[number] = v2(1, 1)

        # --- Rotation ---
        self.rotation: number = 0

        # --- Hidden ---
        self.hidden: bool = False

        # --- Args ---
        self.args: dict = d

        # --- Offset ---
        """
        Index in `sec` of the last frame affected by a `Transformation`

        # TODO: Increased on `wait()` to the highest index of all `Inputs`
        """
        self.lastAffectedFrameIndex: sec = 0

        """
        In `sec`, Increased when flushed.

        # TODO: Flushed on `wait()`
        """
        self.transformationIndexOffset: sec = 0

    def __str__(self) -> str:
        return str(self.__dict__)


class Global:
    """
    Globals used by the classes `Input` and `Transformation`.
    """

    # Represents the steps to generate the video.
    stack: list[dict[str, Any]] = []

    # Index of the next `Input`
    inputCounter: int = 0

    # TODO: last index with an effect

    # --- Automatic Add ---
    automaticAdder = False

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
    Global.stack.append(
        {
            "action": "Wait",
            "n": n,
        }
    )


def automaticAdderOn():
    Global.automaticAdder = True


def automaticAdderOff():
    Global.automaticAdder = False
