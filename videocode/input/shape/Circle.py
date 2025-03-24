#!/usr/bin/env python3


from videocode.input.shape._Shape import *


class circle(Shape):
    def __init__(
        self,
        radius: int = 100,
        thickness: int = 10,
        color: RGBA = BLUE,
        duration: sec = 1,
        filled: bool = False,
    ):
        Global.stack.append(
            {
                "action": "Create",
                "type": "Circle",
                "radius": radius,
                "thickness": thickness,
                "color": color,
                "duration": duration,
                "filled": filled,
            }
        )
