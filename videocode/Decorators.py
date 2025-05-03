#!/usr/bin/env python3


from typing import Any, Callable, TypeAlias

from videocode.Global import Global


# Validators
class Checks:

    def __getitem__(self, x: str) -> Callable:
        # Should define types as classes.
        return self.__getattribute__(x)  # type: ignore

    @staticmethod
    def uint(x: int):
        """positive integer"""
        if x < 0:
            return False
        return True

    @staticmethod
    def uint8(x: int):
        if x < 0 or x > 255:
            return False
        return True

    @staticmethod
    def ufloat(x: float):
        if x < 0:
            return False
        return True

    @staticmethod
    def rgba(x: tuple):
        for i in x:
            if not Checks.uint8(i):
                return False
        return True

    @staticmethod
    def bool(x):
        return isinstance(x, bool)


def typecheck(f: Callable, *args, **kwargs):
    # **Kwargs
    for k, v in kwargs.items():
        typeName: str = f.__annotations__[k].__name__ if isinstance(f.__annotations__[k], type) else str(f.__annotations__[k])
        typeCheck: Callable = Checks()[typeName]
        if not typeCheck(v):
            raise ValueError(f"\n\tin: {args[0].__class__.__name__}\n\tfor: {k}\n\texpected: {typeCheck.__doc__}\n\tgot: {v}")

    # *Args
    for i, v in enumerate(args[1:]):  # Ignore self
        valueName: str = str(list(f.__annotations__.keys())[i])
        typeName: str = str(list(f.__annotations__.values())[i])
        typeCheck: Callable = Checks()[typeName]
        if not typeCheck(v):
            raise ValueError(f"\n\tin: {args[0].__class__.__name__}\n\tfor: {valueName}\n\texpected: {typeCheck.__doc__}\n\tgot: {v}")


def inputCreation(f: Callable):

    def wrapper(*args, **kwargs):

        typecheck(f, *args, **kwargs)

        # Fill the values
        values = kwargs

        for i, v in enumerate(args[1:]):
            values[str(list(f.__annotations__.keys())[i])] = v

        # Use the default ones if not set
        # (The default ones are only set when f is called, but we dont call f)
        for i, k in enumerate(f.__annotations__):
            if k not in values:
                if f.__defaults__ is not None:
                    values[k] = f.__defaults__[i]

        # Generate the stack Creation
        Global.stack.append({"action": "Create", "type": str(args[0].__class__.__name__).title()} | values)

        # Init the Input
        f(*args, **kwargs)

        # Set attr
        for k, v in values.items():
            args[0].__setattr__(k, v)

        return None

    return wrapper


if __name__ == "__main__":
    print(locals())
    # print(globals())
