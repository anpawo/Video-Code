#!/usr/bin/env python3


from videocode.input.Input import *


class video(Input):
    def __init__(self, filepath: str) -> None:
        Global.requiredInputs.append(
            {
                "type": "Video",
                "filepath": filepath,
            }
        )
