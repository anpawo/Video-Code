#!/usr/bin/env python3


from videocode.input.shape._Shape import *


class rectangle(Shape):
    def __init__(
        self,
        width: int = 400,
        height: int = 200,
        thickness: int = 20,
        color: RGBA = BLUE,
        duration: sec = 1,
        cornerRadius: int = 0,  # 0 <= cornerRadius <= 90
        filled: bool = False,
    ):
        Global.stack.append(
            {
                "action": "Create",
                "type": "Rectangle",
                "width": width,
                "height": height,
                "thickness": thickness,
                "color": color,
                "duration": duration,
                "cornerRadius": cornerRadius,
                "filled": filled,
            }
        )


class square:
    def __new__(
        cls,
        *,
        size: int = 200,
        thickness: int = 20,
        color: RGBA = BLUE,
        duration: sec = 1,
        cornerRadius: int = 0,
        filled: bool = False,
    ) -> rectangle:
        return rectangle(size, size, thickness, color, duration, cornerRadius, filled)
