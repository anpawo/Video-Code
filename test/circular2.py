#!/usr/bin/env python3


from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from circular1 import A


class B:
    def __init__(self, a: A | None = None):
        self.a = a
