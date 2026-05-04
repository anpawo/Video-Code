#!/usr/bin/env python3

from typing import Any, Callable, TypeVar, overload

T = TypeVar("T")

@overload
def autoProp(
    setterCallback: Callable[..., Any] | None = ...,
    getMod: None = ...,
) -> Callable[[Callable[..., T]], T]: ...
@overload
def autoProp(
    setterCallback: Callable[..., Any] | None = ...,
    getMod: Callable[[Any, T], T] = ...,
) -> Callable[[Callable[..., T]], T]: ...
