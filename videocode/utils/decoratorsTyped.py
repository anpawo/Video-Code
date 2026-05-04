#!/usr/bin/env python3

from typing import Any, Callable

from videocode.ty import maybe


def autoProp(
    setterCallback: maybe[Callable[[Any], Any]] = None,
    getMod: maybe[Callable[[Any, Any], Any]] = None,
):
    """
    Decorator that generates a property + setter for a given name.
    """

    def decorator(func):
        attrName = func.__name__
        privateName = f"_{attrName}"

        def getter(self) -> Any:
            if getMod:
                return getMod(self, getattr(self, privateName))
            return getattr(self, privateName)

        def setter(self, value):
            object.__setattr__(self, privateName, value)
            if setterCallback:
                setterCallback(self)

        return property(getter, setter)

    return decorator
