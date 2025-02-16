#!/usr/bin/env python3


from frontend.input._Input import *


class formula(Input):
    def __init__(self, f: str) -> None:
        Global.variable.append(("Formula", [f]))
