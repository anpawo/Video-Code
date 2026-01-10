#!/usr/bin/env python3


import json
import sys


sys.path.append(".")


from globals import *
from videocode import *


def makeSerializable(o):
    return o.makeSerializable()


def serializeScene(filepath: str) -> str:
    """
    Serialiaze a file representing a `Scene`.
    """

    # Read the content of the file
    with open(filepath, "r") as file:
        content = file.read()  # TODO: Replace comments with labels

    # Exec the file representing the `Scene`. It will update the globals in `Global`.
    global __name__
    __name__ = "Scene"
    code = compile(content, filepath, "exec")
    exec(code, globals())

    # Access Stack
    g = Global()

    # Serialize the instructions to JSON
    return json.dumps(g.stack, default=makeSerializable)


if __name__ == "__main__":

    for i in json.loads(serializeScene("video.py")):
        print(i)
