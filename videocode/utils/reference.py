#!/usr/bin/env python3


from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from input.input import Input


class Reference:
    def __init__(self, input: Input) -> None:
        self.input = input

    def __getattribute__(self, name: str) -> str:
        return name
