#!/usr/bin/env python3


from typing import Type


import json
import inspect
import sys

sys.path.append(".")

from VideoCode import *


def commentsToLabel(s: str) -> str:
    if s == "":
        return ""
    if s[0:3] != "\n# ":
        return s[0] + commentsToLabel(s[1:])
    i = 3
    while s[i] != "\n":
        i += 1
    return f'label("{s[3:i]}")' + commentsToLabel(s[i:])


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
    exec(content, globals())

    # Access Globals: `variable` and `stack`
    g = Global()

    # Serialize the instructions to JSON
    return json.dumps(
        {
            "requiredInputs": g.requiredInputs,
            "actionStack": g.actionStack,
        }
    )


if __name__ == "__main__":
    for k, v in json.loads(serializeScene("video.py")).items():
        print(f"{k}")
        for i in v:
            print(f"   {i}")
