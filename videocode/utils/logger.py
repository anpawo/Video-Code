#!/usr/bin/env python3


from sys import stderr


class Logger:
    def __init__(self, prefix: str, color: str, file=stderr) -> None:
        self.prefix = prefix
        self.color = color
        self.file = file

    def log(self, s: str):
        print(f"{self.color}[{self.prefix}]:\033[0m {s}", file=self.file)


TEXT_GREEN = "\033[36m"

DEBUG = Logger(prefix="Debug", color=TEXT_GREEN)
