#!/usr/bin/env python3


import time


from typing import TYPE_CHECKING, Callable
from videocode.context import Context
from videocode.utils.funcutils import upperFirst
from videocode.utils.timeit import *
from videocode.ty import *
from videocode.utils.logger import *


if TYPE_CHECKING:
    from videocode.input.input import Input


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


def inputCreation(f: Callable[..., None]):
    """
    Automate the `Input` creation.
    """

    def wrapper(self: "Input", *args, **kwargs):  # need the string type because autoCppAttrs would bug
        # Input's init
        f(self, *args, **kwargs)

        # Generate the stack creation
        Context.stack.append(
            {
                "action": "Create",
                "type": self.cppName,
                "args": {k: v for k, v in self.__dict__.items() if k in self.cppAttrs},
                "hide": Context.waitOffset > 0,
            },
        )

        # If created mid-timeline (after a flush), hide until the current offset
        if Context.waitOffset > 0:
            self.show()  # add start ?

    return wrapper


def sandboxFlush(f):
    def wrapper(self, *args, **kwargs):
        transformationOffset = self.meta.transformationOffset
        lastAffectedFrame = self.meta.lastAffectedFrame

        result = f(self, *args, **kwargs)

        self.meta.transformationOffset = transformationOffset
        self.meta.lastAffectedFrame = lastAffectedFrame

        return result

    return wrapper


def setAttrOn(f):
    def wrapper(self: Input, *args, **kwargs):
        setattrCallbackOn = self.meta.setattrCallbackOn

        self.meta.setattrCallbackOn = True
        result = f(self, *args, **kwargs)

        self.meta.setattrCallbackOn = setattrCallbackOn

        return result

    return wrapper


def trackProps(initFunc, autoInit=True):
    """
    Decorator that keeps track of the props of a class on creation.

    Also inits the props with the default value given in init if any.
    """

    def wrapper(self, *args, **kwargs):
        self.meta.props = {name for cls in type(self).__mro__ for name, val in vars(cls).items() if isinstance(val, property)}

        # If False, the class does some shenanigans with the args before settings the attr.
        if autoInit:
            # match args to param names via __code__
            paramNames = initFunc.__code__.co_varnames[1 : initFunc.__code__.co_argcount]  # skip 'self' and local var
            defaults = initFunc.__defaults__ or ()

            # defaults align to the END of paramNames
            defaultOffset = len(paramNames) - len(defaults)
            defaultMap = {paramNames[i + defaultOffset]: defaults[i] for i in range(len(defaults))}

            params = defaultMap | dict(zip(paramNames, args)) | kwargs
            for paramName, paramValue in params.items():
                if paramName in self.meta.props:
                    object.__setattr__(self, f"_{paramName}", paramValue)

        initFunc(self, *args, **kwargs)

    return wrapper


def autoProp(setterCallback=None):
    """
    Decorator that generates a property + setter for a given name.
    """

    def decorator(func):
        attrName = func.__name__
        privateName = f"_{attrName}"

        def getter(self):
            return getattr(self, privateName)

        def setter(self, value):
            object.__setattr__(self, privateName, value)
            if setterCallback:
                setterCallback(self)

        return property(getter, setter)

    return decorator


def timed(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        DEBUG.log(f"[TIMED] {func.__qualname__}: {elapsed:.6f}s")
        return result

    return wrapper


if __name__ == "__main__":
    print(locals())
    # print(globals())
