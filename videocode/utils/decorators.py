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
            self.apply(hide(), start=0, offset=0)
            self.waitTo(Context.waitOffset).show()

    return wrapper


_CLASS_T = TypeVar("_CLASS_T")
_ATTR1_T = TypeVar("_ATTR1_T")
_ATTR2_T = TypeVar("_ATTR2_T")
_ATTR3_T = TypeVar("_ATTR3_T")
_ATTR4_T = TypeVar("_ATTR4_T")


class prop(Generic[_CLASS_T, _ATTR1_T, _ATTR2_T]):
    @overload
    def __init__(self, *, onSet: Callable[[Any], None]) -> None:
        """
        The default `onSet` is made for simple callbacks that do not need to know what value was assigned to the attribute.

        If you want an advanced callback reaction: use `attribute.setter`.
        """
        ...

    @overload
    def __init__(self) -> None: ...

    def __init__(self, *, onSet: Callable[[_CLASS_T], None] | None = None) -> None:
        self.onSet: Callable[[_CLASS_T, _ATTR1_T], None] | None = None if onSet is None else lambda s, _: onSet(s)
        self.onGet: Callable[[_CLASS_T, _ATTR1_T], _ATTR2_T] | None = None
        self.privateName: str = ""

    @overload
    def __call__(self, func: Callable[[], _ATTR3_T], /) -> prop[_CLASS_T, _ATTR3_T, _ATTR3_T]: ...  # stub
    @overload
    def __call__(self, func: Callable[[Any, _ATTR3_T], _ATTR4_T], /) -> prop[_CLASS_T, _ATTR3_T, _ATTR4_T]: ...  # onGet

    def __call__(self, func: Callable) -> Any:
        self.privateName = f"_{func.__name__}"
        isStub = func.__code__.co_argcount == 0
        if not isStub:
            self.onGet = func
        return self

    @overload
    def __get__(self: prop[_CLASS_T, _ATTR1_T, _ATTR2_T], instance: None, owner: type, /) -> prop[_CLASS_T, _ATTR1_T, _ATTR2_T]: ...
    @overload
    def __get__(self: prop[_CLASS_T, _ATTR1_T, _ATTR2_T], instance: Any, owner: type, /) -> _ATTR2_T: ...

    def __get__(self, instance, owner, /):
        attr = object.__getattribute__(instance, self.privateName)
        if self.onGet is not None:
            return self.onGet(instance, attr)
        return attr

    def __set__(self, instance: Any, value: _ATTR1_T, /) -> None:
        isInitialized = hasattr(instance, self.privateName)
        # Skip storage + onSet entirely when the value hasn't changed.
        # Avoids redundant geometry rebuilds (e.g. unchanged chars in textSetter).
        if isInitialized and self.onSet is not None:
            if object.__getattribute__(instance, self.privateName) == value:
                return
        object.__setattr__(instance, self.privateName, value)
        if isInitialized and self.onSet is not None:
            self.onSet(instance, value)

    def setter(self, onSet: Callable[[_CLASS_T, _ATTR1_T], None], /) -> Self:
        self.onSet = onSet
        return self


class autoProp(prop[_CLASS_T, _CLASS_T, _CLASS_T]):
    def __init__(self, func: Callable[[], _CLASS_T], /):
        super().__init__()
        self.privateName = f"_{func.__name__}"


class propagate(prop[_CLASS_T, _ATTR1_T, _ATTR2_T]):
    """
    Like prop, but also broadcasts the new value down to all children on set.
    """

    def __init__(self, func: Callable[[], _CLASS_T], /):
        super().__init__()
        self.__call__(func)

    def __call__(self, func: Callable[[], _CLASS_T]) -> Any:
        super().__call__(func)
        attr = func.__name__

        def callback(instance, value):
            instance.broadcast(lambda self: self.broadcast(lambda self: setattr(self, attr, value)))

        self.onSet = callback
        return self


if __name__ == "__main__":
    print(locals())
    # print(globals())
