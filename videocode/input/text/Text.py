#!/usr/bin/env python3


from typing import Optional


from videocode.Constant import *
from videocode.input.Input import *


class text(Input):
    def __init__(
        self,
        s: str,
        /,
        *,
        fontSize: float = 1,
        color: RGBA = WHITE,
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
