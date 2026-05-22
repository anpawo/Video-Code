#!/usr/bin/env python3


import json
import sys


sys.path.append(".")


from videocode.context import *
from videocode import *


def _resetContext():
    Context.stack = []
    Context.inputCounter = 0
    Context.lastEverAffectedFrame = 0
    Context.waitOffset = 0


def execScene(filepath: str) -> None:
    """
    Execute the scene file and populate Context.stack.
    C++ reads the stack directly via pybind11 — no JSON serialization.
    """
    _resetContext()

    with open(filepath, "r") as file:
        content = file.read()

    global __name__
    __name__ = "Scene"
    code = compile(content, filepath, "exec")
    exec(code, globals())


def serializeScene(filepath: str) -> str:
    """
    Serialiaze a file representing a `Scene`.
    """
    _resetContext()

    # Read the content of the file
    with open(filepath, "r") as file:
        content = file.read()

    # Exec the file representing the `Scene`. It will update the globals in `Global`.
    global __name__
    __name__ = "Scene"
    code = compile(content, filepath, "exec")
    exec(code, globals())

    # Access Stack
    g = Context()

    # Serialize the instructions to JSON
    return json.dumps(g.stack, default=lambda x: x.jsonSerialization())


if __name__ == "__main__":

    for i in json.loads(serializeScene("video.py")):
        print(i, file=sys.stderr)
