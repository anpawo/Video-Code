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
    def _resolve_checker(ann) -> Callable:
        # ann can be a plain type or a typing annotation; try to map to a Checks method
        try:
            if isinstance(ann, type):
                name = ann.__name__
                if name == "int":
                    return lambda x: isinstance(x, int)
                if name == "float":
                    return lambda x: isinstance(x, (int, float))
                if name == "str":
                    return lambda x: isinstance(x, str)
                if name == "bool":
                    return Checks().bool
                # try to use Checks method with same name
                try:
                    return Checks()[name]
                except Exception:
                    return lambda x: True
            else:
                s = str(ann)
                if "uint8" in s:
                    return Checks().uint8
                if "uint" in s:
                    return Checks().uint
                if "ufloat" in s:
                    return Checks().ufloat
                if "rgba" in s:
                    return Checks().rgba
                if "bool" in s:
                    return Checks().bool
        except Exception:
            pass
        return lambda x: True

    # **Kwargs
    for k, v in kwargs.items():
        ann = f.__annotations__.get(k)
        checker = _resolve_checker(ann)
        try:
            ok = checker(v)
        except Exception:
            ok = False
        if not ok:
            raise ValueError(f"\n\tin: {args[0].__class__.__name__}\n\tfor: {k}\n\texpected: {getattr(checker, '__doc__', '')}\n\tgot: {v}")

    # *Args
    for i, v in enumerate(args[1:]):  # Ignore self
        keys = list(f.__annotations__.keys())
        vals = list(f.__annotations__.values())
        if i >= len(keys):
            continue
        valueName: str = str(keys[i])
        ann = vals[i]
        checker = _resolve_checker(ann)
        try:
            ok = checker(v)
        except Exception:
            ok = False
        if not ok:
            raise ValueError(f"\n\tin: {args[0].__class__.__name__}\n\tfor: {valueName}\n\texpected: {getattr(checker, '__doc__', '')}\n\tgot: {v}")


def inputCreation(f: Callable):
    def wrapper(*args, **kwargs):
        typecheck(f, *args, **kwargs)

        # Fill the values (work on a copy so we don't mutate the original kwargs passed to f)
        values = kwargs.copy()

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
