#!/usr/bin/env python3


import time


from sys import stderr


class timeit:
    def __init__(self, context: str = "timeit"):
        self.context = context

    def __enter__(self):
        self.start = time.perf_counter()

    def __exit__(self, *_):
        elapsed = (time.perf_counter() - self.start) * 1_000
        print(f"{self.context}: {elapsed:.3f} ms", file=stderr)


if __name__ == "__main__":
    with timeit("test"):
        print("hello")
