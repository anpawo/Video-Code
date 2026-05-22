#!/usr/bin/env python3


from sys import stderr
from typing import Any


class Logger:
    def __init__(self, prefix: str, color: str, file=stderr) -> None:
        self.prefix = prefix
        self.color = color
        self.file = file

    def log(self, s: str):
        print(f"{self.color}[{self.prefix}]:\033[0m {s}", file=self.file)

    def __call__(self, s: str) -> None:
        self.log(s)


TEXT_GREEN = "\033[36m"
