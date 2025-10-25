#!/usr/bin/env python3


from typing import Callable, Self


class composition:
    """
    Function_Composition

    g | compose | f   =>   f . g   =>   f(g())
    """

    def __init__(self) -> None:
        self.g: Callable

    def __ror__(self, g: Callable) -> Self:
        self.g = g
        return self

    def __or__(self, f: Callable) -> Callable:
        def fg(*args, **kwargs):
            return f(self.g(*args, **kwargs))

        return fg


compose = composition()
