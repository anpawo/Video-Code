#!/usr/bin/env python3


class uint(int):
    """Unsigned integer (>=0) with runtime checks."""

    def __new__(cls, value: int):
        if value < 0:
            raise ValueError("uint must be >= 0")
        return super().__new__(cls, value)


a: uint = 5

print(a)
