#!/usr/bin/env python3


from videocode.input.Input import *


class image(Input):
    def __init__(self, filepath: str) -> None:
        Global.requiredInputs.append(
            {
                "type": "Image",
                "filepath": filepath,
            }
        )
