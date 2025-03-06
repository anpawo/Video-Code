#!/usr/bin/env python3


from videocode.input.Input import *


class formula(Input):
    def __init__(self, f: str) -> None:
        Global.stack.append(("Formula", [f]))
