#!/usr/bin/env python3


from typing import Optional


from videocode.Constant import RGBA, WHITE
from videocode.input.Input import *


class text(Input):
    def __init__(self, s: str, fontSize: float = 1, color: RGBA = WHITE, fontThickness: Optional[int] = None) -> None:
        Global.requiredInputs.append(
            {
                "type": "Text",
                "text": s,
                "fontSize": fontSize,
                "color": color,
                "fontThickness": fontThickness or fontSize * 2,
            }
        )
