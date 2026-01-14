#!/usr/bin/env python3


from typing import Type


import json
import sys

sys.path.append(".")

from videocode.VideoCode import *


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

    # Access Stack
    g = Global()

    # Serialize the instructions to JSON
    return json.dumps(g.stack)


if __name__ == "__main__":
    for i in json.loads(serializeScene("video.py")):
        print(i)
