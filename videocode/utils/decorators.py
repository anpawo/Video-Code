#!/usr/bin/env python3


import functools
import time


from typing import TYPE_CHECKING, Callable, Concatenate, Generic, ParamSpec, TypeVar
from typing_extensions import Self
from videocode.constants import SINGLE_FRAME
from videocode.context import Context
from videocode.ty import *
from videocode.utils.funcutils import upperFirst
from videocode.utils.logger import *
from videocode.shader.vertexShader.hide import hide


if TYPE_CHECKING:
    from videocode.input.input import Input


_P = ParamSpec("_P")
_T = TypeVar("_T", bound="Input")


def inputCreation(f: Callable[Concatenate[_T, _P], None]) -> Callable[Concatenate[_T, _P], None]:
    """
    Automate the `Input` creation.
    """

    @functools.wraps(f)
    def wrapper(self: _T, *args: _P.args, **kwargs: _P.kwargs) -> None:
        # Input's init
        f(self, *args, **kwargs)

        # Generate the stack creation
        Context.create(
            inputType=self.cppName,
            inputArgs={k: v for k, v in self.__dict__.items() if k in self.cppAttrs},
        )

        # If created mid-timeline (after a flush), hide until the current offset
        if Context.waitOffset > 0:
            Context.apply(self.meta.index, upperFirst(hide.__name__), hide._type, {"start": 0, "duration": hide.duration})
            self.waitTo(Context.waitOffset).show()

    return wrapper


def trackProps(initFunc: Callable[Concatenate[_T, _P], None], autoInit=True) -> Callable[Concatenate[_T, _P], None]:
    """
    Decorator that keeps track of the props of a class on creation.

    Also inits the props with the default value given in init if any.
    """

    @functools.wraps(initFunc)
    def wrapper(self: _T, *args: _P.args, **kwargs: _P.kwargs) -> None:
        self.meta.props = {name for cls in type(self).__mro__ for name, val in vars(cls).items() if isinstance(val, (property, prop, autoProp))}

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


def setAttrOn(f):
    @functools.wraps(f)
    def wrapper(self: Input, *args, **kwargs):
        setattrCallbackOn = self.meta.setattrCallbackOn

        self.meta.setattrCallbackOn = True
        result = f(self, *args, **kwargs)

        self.meta.setattrCallbackOn = setattrCallbackOn

        return result

    return wrapper


_CLASS_T = TypeVar("_CLASS_T")
_ATTR1_T = TypeVar("_ATTR1_T")
_ATTR2_T = TypeVar("_ATTR2_T")


class prop(Generic[_CLASS_T, _ATTR1_T]):
    @overload
    def __init__(self, *, onSet: Callable[[Any], None]) -> None: ...
    @overload
    def __init__(self) -> None: ...

    def __init__(self, *, onSet: Callable[[_CLASS_T], None] | None = None) -> None:
        self.onSet: Callable[[_CLASS_T, _ATTR1_T], None] | None = None if onSet is None else lambda s, _: onSet(s)
        self.onGet: Callable[[_CLASS_T, _ATTR1_T], _ATTR1_T] | None = None
        self.privateName: str = ""

    @overload
    def __call__(self, func: Callable[[], _ATTR2_T], /) -> prop[_CLASS_T, _ATTR2_T]: ...  # stub
    @overload
    def __call__(self, func: Callable[[_CLASS_T, _ATTR2_T], _ATTR2_T], /) -> prop[_CLASS_T, _ATTR2_T]: ...  # onGet

    def __call__(self, func: Callable) -> Any:
        self.privateName = f"_{func.__name__}"
        isStub = func.__code__.co_argcount == 0

        if not isStub:
            self.onGet = func

        return self

    @overload
    def __get__(self: prop[_CLASS_T, _ATTR1_T], instance: None, owner: type, /) -> prop[_CLASS_T, _ATTR1_T]: ...
    @overload
    def __get__(self: prop[_CLASS_T, _ATTR1_T], instance: Any, owner: type, /) -> _ATTR1_T: ...

    def __get__(self, instance, owner, /):
        if self.onGet is not None:
            return self.onGet(instance, getattr(instance, self.privateName))
        return getattr(instance, self.privateName)

    def __set__(self, instance: Any, value: _ATTR1_T, /) -> None:
        object.__setattr__(instance, self.privateName, value)
        if self.onSet is not None:
            self.onSet(instance, value)

    def setter(self, onSet: Callable[[_CLASS_T, _ATTR1_T], None], /) -> Self:
        self.onSet = onSet
        return self


class autoProp(Generic[_CLASS_T]):
    def __new__(cls, func: Callable[..., _CLASS_T], /) -> Self:
        instance = object.__new__(cls)
        return instance

    def __init__(self, func: Callable[[], _CLASS_T], /):
        self.privateName = f"_{func.__name__}"

    def __get__(self, instance: Any, owner: type) -> _CLASS_T:
        return getattr(instance, self.privateName)

    def __set__(self, instance: Any, value: _CLASS_T) -> None:
        object.__setattr__(instance, self.privateName, value)


if __name__ == "__main__":
    print(locals())
    # print(globals())
