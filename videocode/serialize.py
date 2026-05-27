#!/usr/bin/env python3


import json
import sys


sys.path.append(".")


from videocode.context import *
from videocode import *


def _resetContext():
    Context.stack = []
    Context._applyIndex = {}
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

    import os
    if os.environ.get("VC_PROFILE"):
        import cProfile, pstats, io
        pr = cProfile.Profile()
        pr.enable()
        exec(code, globals())
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.print_stats(30)
        print("[profile] Top 30 cumulative:\n" + s.getvalue(), flush=True)
    else:
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
