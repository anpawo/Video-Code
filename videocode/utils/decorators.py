#!/usr/bin/env python3


from sys import stderr
from typing import TYPE_CHECKING, Any, Callable
from videocode.globals import Global
from videocode.utils.funcutils import fromWorlToScreen, upperFirst
from videocode.utils.timeit import *
from videocode.ty import *


if TYPE_CHECKING:
    from videocode.input.Input import Input


# Validators
class Checks:

    def __getitem__(self, x: str) -> Callable:
        # Should define types as classes.
        if "'" in x:
            x = x.split("'")[1]
        return self.__getattribute__(x)

    @staticmethod
    def uint(x: int):
        """positive integer"""
        if x < 0:
            return False
        return True

    @staticmethod
    def wuint(x: int):
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
    def wufloat(x: float):
        if x < 0:
            return False
        return True

    @staticmethod
    def rgba(c: rgba):
        return Checks.uint8(c.r) and Checks.uint8(c.g) and Checks.uint8(c.b) and Checks.uint8(c.a)

    @staticmethod
    def bool(x):
        return isinstance(x, bool)

    # Nothing
    @staticmethod
    def str(x):
        return True


# def typecheck(f: Callable, *args, **kwargs):
#     # **Kwargs
#     for k, v in kwargs.items():
#         typeName: str = f.__annotations__[k].__name__ if isinstance(f.__annotations__[k], type) else str(f.__annotations__[k])
#         typeCheck: Callable = Checks()[typeName]
#         if not typeCheck(v):
#             raise ValueError(f"\n\tin: {args[0].__class__.__name__}\n\tfor: {k}\n\texpected: {typeCheck.__doc__}\n\tgot: {v}")

#     # *Args
#     for i, v in enumerate(args[1:]):  # Ignore self
#         valueName: str = str(list(f.__annotations__.keys())[i])
#         typeName: str = str(list(f.__annotations__.values())[i])
#         typeCheck: Callable = Checks()[typeName]
#         if not typeCheck(v):
#             raise ValueError(f"\n\tin: {args[0].__class__.__name__}\n\tfor: {valueName}\n\texpected: {typeCheck.__doc__}\n\tgot: {v}")


# def bindArgs(f: Callable, *args, **kwargs) -> tuple[Input, dict[str, Any]]:
#     attrs: dict[str, Any] = {}
#     input: Input = args[0]

#     argNames = list(f.__annotations__.keys())
#     defaults = f.__defaults__ or ()

#     for i in range(-len(defaults), 0):
#         attrs[argNames[i]] = defaults[i]

#     # *args
#     for name, value in zip(argNames, args[1:]):  # skip self
#         attrs[name] = value

#     # **kargs
#     for k, v in kwargs.items():
#         attrs[k] = v

#     # attrs from init()
#     for k, v in input.__dict__.items():
#         if k != "meta":
#             attrs[k] = v

#     # input's attrs
#     for k, v in attrs.items():
#         object.__setattr__(input, k, v)

#     return input, attrs


def inputCreation(f: Callable[..., None]):
    """
    Automate the `Input` creation.
    """

    def inputCreationWrapper(*args, **kwargs):
        # Input's init
        f(*args, **kwargs)

        # Input
        input = args[0]
        attrs = {k: v for k, v in input.__dict__.items() if k != "meta"}

        # Incorporate the annotations of the init function into the class
        for k in f.__annotations__:
            input.__class__.__annotations__[k] = f.__annotations__[k]

        # Generate the stack creation
        Global.stack.append(
            {
                "action": "Create",
                "type": upperFirst(input.__class__.__name__),
                "args": fromWorlToScreen(f.__annotations__, attrs),
            },
        )

    return inputCreationWrapper


if __name__ == "__main__":
    print(locals())
    # print(globals())
