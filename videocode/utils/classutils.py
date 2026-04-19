#!/usr/bin/env python3


from sys import stderr
import weakref


from typing import Callable, Self, TypeVar, cast, overload


class Tracker[T]:
    def __init__(self, value: T = None, callback: Callable | None = None):
        self.default = value
        self.defaultCallback = callback
        self.instances: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()

    def __set_name__(self, owner, name):
        self.name = name

    @overload
    def __get__(self, obj: None, objtype) -> Self: ...
    @overload
    def __get__(self, obj: object, objtype) -> T: ...
    def __get__(self, obj, objtype=None) -> T | Self:
        if obj is None:
            return self
        entry = self.instances.get(obj)
        return entry["value"] if entry else self.default

    def __set__(self, obj, value):
        print(f"set, {obj}, {value}", file=stderr)
        if isinstance(value, Tracker):
            self.instances[obj] = {"value": value.default, "callback": value.defaultCallback}
        else:
            if obj in self.instances:
                self.instances[obj]["value"] = value
                self.instances[obj]["callback"](value)
            else:
                self.instances[obj] = {"value": value, "callback": self.defaultCallback}
