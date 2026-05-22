#!/usr/bin/env python3


import time


from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar, cast
from videocode.constants import DEBUG, SINGLE_FRAME
from videocode.ty import frame, maybe


if TYPE_CHECKING:
    from videocode.ty import sec
    from videocode.input.input import Input


class AttributeNameReference:
    """
    Prevent Attribute Name Missmatch
    """

    def __init__(self, _: Input): ...

    def __getattribute__(self, name: str) -> str:
        return name


class timeit:
    def __init__(self, context: str = "took"):
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
    Prevent `None` checks.

    Like `Value or Default` but only truthy if `value is None`.

    Examples:
    ---
    >>> Maybe(value) | defaultValue
    >>> Maybe(value).map(func).get()
    >>> Maybe(value).map(func).orElse(defaultValue)
    """

    def __init__(self, value: _MAYBE_T_VAL | None) -> None:
        self.value = value

    def __or__(self, default: _MAYBE_T_VAL) -> _MAYBE_T_VAL:
        if self.value is None:
            return default
        return self.value

    def map(self, func: Callable[[_MAYBE_T_VAL], _MAYBE_T_RET]) -> Maybe[_MAYBE_T_RET]:
        if self.value is None:
            return Maybe(None)
        return Maybe(func(self.value))

    def get(self) -> _MAYBE_T_VAL | None:
        return self.value

    def orElse(self, default: _MAYBE_T_VAL) -> _MAYBE_T_VAL:
        return self | default


_AT_T = TypeVar("_AT_T", default=Any)


class At(Generic[_AT_T]):
    def __new__(cls, *args, **kwargs) -> _AT_T:
        return cast(_AT_T, super().__new__(cls))

    def __init__(self, start: sec, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> None:
        self.value: _AT_T = cast(_AT_T, None)
        self.start = start
        self.duration = duration
        self.offset = offset

    def __rmatmul__(self, value: _AT_T) -> _AT_T:
        """
        Clean way to use `At`.

        `value @ At(start, duration, offset)`
        """
        self.value = value
        return cast(_AT_T, self)

    def __or__(self, value: _AT_T) -> _AT_T:
        """
        Second way to use `At` if `__matmul__` is defined on the type of `value`.

        `At(start, duration, offset) | value`
        """
        self.value = value
        return cast(_AT_T, self)

    def unpack(self) -> tuple[_AT_T, sec, sec, maybe[frame]]:
        return self.value, self.start, self.duration, self.offset
