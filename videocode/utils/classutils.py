#!/usr/bin/env python3


import time


from functools import wraps
from types import UnionType
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar, cast
from videocode.ty import *
from videocode.utils.logger import DEBUG


if TYPE_CHECKING:
    from videocode.input.input import Input


class AttributeNameReference:
    """
    Prevent Attribute Name Missmatch
    """

    def __init__(self, _: Input): ...

    def __getattribute__(self, name: str) -> str:
        return name


class timeit:
    def __init__(self, context: str = "timeit"):
        self.context = context
        self.start: float

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *_):
        elapsed = (time.perf_counter() - self.start) * 1_000
        DEBUG.log(f"{self.context}: {elapsed:.3f} ms")

    def __call__(self, func):
        """Allow usage as a decorator"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            DEBUG.log(f"[TIMED] {func.__qualname__}: {elapsed:.6f}s")
            return result

        return wrapper


_MAYBE_T_VAL = TypeVar("_MAYBE_T_VAL")
_MAYBE_T_RET = TypeVar("_MAYBE_T_RET")


class Maybe(Generic[_MAYBE_T_VAL]):
    """
    Prevent None Checks

    Like `Value or Default` but only truthy if `value is None`
    """

    def __init__(self, value: _MAYBE_T_VAL | None) -> None:
        self.value = value

    def __or__[T](self, value: T) -> T | _MAYBE_T_VAL:
        if self.value is None:
            return value
        return self.value

    def map(self, func: Callable[[_MAYBE_T_VAL], _MAYBE_T_RET]) -> Maybe[_MAYBE_T_RET]:
        if self.value is None:
            return Maybe(None)
        return Maybe(func(self.value))

    def get(self) -> _MAYBE_T_VAL | None:
        return self.value

    def orElse(self, default: _MAYBE_T_VAL) -> _MAYBE_T_VAL:
        if self.value is None:
            return default
        return self.value
