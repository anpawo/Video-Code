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
    Serialiaze the `Scenes` of a file.
    """

    # Read the content of the file
    with open(filepath, "r") as file:
        content = file.read()  # TODO: Replace comments with labels

    # Exec the file to register the `Scene`
    global __name__
    __name__ = "Scene"
    exec(content, globals())

    # Filter out anything other that the `Scenes`
    scenes: list[Type[Scene]] = [v for _, v in globals().items() if inspect.isclass(v) and Scene in v.__bases__]

    # Temporary load the first `Scene` found. TODO: load the desired scene in the future
    scenes[0]().scene()

    # Access Globals: `variable` and `stack`
    g = Global()

    # Serialize the instructions to JSON
    return json.dumps(
        {
            "variable": g.variable,
            "stack": g.stack,
        }
    )


if __name__ == "__main__":
    for k, v in json.loads(serializeScene("video.py")).items():
        print(f"{k:<12}{v}")
