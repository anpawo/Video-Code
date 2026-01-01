#!/usr/bin/env python3


from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from circular2 import B


class A:
    def __init__(self, b: B | None = None):
        self.b = b


if __name__ == "__main__":
    a = A()
