#!/usr/bin/env python3


from typing import Any


class Test:
    def __init__(self) -> None:
        self.x: int = 1

    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)


t = Test()

print(t.x)

t.x = 2

print(t.x)
