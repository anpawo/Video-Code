#!/usr/bin/env python3


from videocode.input.Input import *


class video(Input):
    def __init__(self, filepath: str) -> None:
        Global.stack.append(
            {
                "action": "Create",
                "type": "Video",
                "filepath": filepath,
            }
        )
