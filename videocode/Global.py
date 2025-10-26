#!/usr/bin/env python3


import copy
from typing import Any
from videocode.Constant import *


class Metadata:
    def __init__(self, *, x: position, y: position) -> None:
        # --- Position ---
        self.x: position = x
        self.y: position = y

        # --- Align ---
        # Center, Left, Right, Top, Bottom
        self.alignX: align = CENTER
        self.alignY: align = CENTER

        # --- Opacity ---
        self.opacity: uint = 255

        # --- Rotation --- ?

    def __str__(self) -> str:
        return f"x={self.x}, y={self.y}"


class Global:
    """
    Globals used by the classes `Input` and `Transformation`.
    """

    # Represents the steps to generate the video.
    stack: list[dict[str, Any]] = []

    # Index of the next `Input`
    inputCounter: int = 0

    # Default Metadata
    defaultMetadata: Metadata = Metadata(x=SW * 0.5, y=SH * 0.5)

    # --- Automatic Add ---
    automaticAdder = False

    @staticmethod
    def getIndex() -> int:
        Global.inputCounter += 1
        return Global.inputCounter - 1

    @staticmethod
    def getDefaultMetadata() -> Metadata:
        return copy.deepcopy(Global.defaultMetadata)

    def __str__(self) -> str:
        return f"Stack={self.stack}"

    def __repr__(self) -> str:
        return str(self)


def wait(n: sec = 1) -> None:
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
