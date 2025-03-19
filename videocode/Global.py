#!/usr/bin/env python3


from typing import Any


class Global:
    """
    Globals used by the classes `Input` and `Transformation`.
    """

    # Represents the steps to generate the video.
    stack: list[dict[str, Any]] = []

    # Index of the next `Input`
    inputCounter: int = 0

    @staticmethod
    def getIndex() -> int:
        Global.inputCounter += 1
        return Global.inputCounter - 1

    def __str__(self) -> str:
        return f"Stack={self.stack}"

    def __repr__(self) -> str:
        return str(self)


def wait(n: int = 1) -> None:
    Global.stack.append(
        {
            "action": "Wait",
            "n": n,
        }
    )
