#!/usr/bin/env python3


from typing import Optional


from videocode.Constant import *
from videocode.Decorators import inputCreation
from videocode.input.Input import *


class text(Input):

    # @inputCreation
    def __init__(
        self,
        s: str,
        fontSize: float = 1,
        color: rgba = WHITE,
        fontThickness: Optional[int] = None,
        duration: sec = 1,
    ):
        Global.stack.append(
            {
                "action": "Create",
                "type": "Text",
                "text": s,
                "fontSize": fontSize,
                "color": color,
                "fontThickness": fontThickness or fontSize * 2,
                "duration": duration,
            }
        )
