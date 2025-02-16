#!/usr/bin/env python3

import sys
import inspect
from typing import Type

from VideoCode import *


class Video(Scene):
    def __init__(self) -> None:
        print("child")


class Image: ...


# eval(s)

scenes: list[Type[Scene]] = [v for _, v in globals().items() if inspect.isclass(v) and Scene in v.__bases__]


print(scenes)
for i in scenes:
    s = i()
    print(Globals.stack)
    s.__stack.append("test")
    print(Globals.stack)
