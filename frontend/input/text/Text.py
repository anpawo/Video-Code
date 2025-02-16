#!/usr/bin/env python3


from typing import Optional


from frontend.input._Input import *


class text(Input):
    def __init__(self, s: str, /, *, font: Optional[str] = None, fontSize: Optional[int] = None) -> None:
        Global.variable.append(("Text", [s]))
