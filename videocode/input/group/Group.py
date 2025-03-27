#!/usr/bin/env python3


from videocode.input.Input import *


class group(Input):
    def __init__(self, *inputs: Input):
        Global.stack.append(
            {
                "action": "Create",
                "type": "Group",
                "inputs": [i.index for i in inputs],
            }
        )
