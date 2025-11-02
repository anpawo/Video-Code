import inspect

from videocode import VideoCode
from videocode.Decorators import Checks, inputCreation, typecheck
from videocode.Global import Global


def test_videocode_import():
    # importing VideoCode should not raise and should expose some names
    assert hasattr(VideoCode, "Global")


def test_checks_getitem_and_validators():
    c = Checks()
    # __getitem__ should return callable attributes when present
    assert callable(c["uint"]) or callable(getattr(c, "uint"))
    assert c.uint(5)
    assert not c.uint(-1)
    assert c.uint8(0)
    assert not c.uint8(300)
    assert c.ufloat(0.1)
    assert not c.ufloat(-0.1)
    assert c.bool(True)


def test_inputcreation_decorator_sets_stack():
    Global.stack.clear()

    class Dummy:
        def __init__(self):
            self.value = None

        @inputCreation
        def make(self, filepath: str):
            self.value = filepath

    d = Dummy()
    d.make("/tmp/x")
    assert Global.stack[-1]["action"] == "Create"
    assert d.value == "/tmp/x"


def test_typecheck_raises_on_bad_type():
    def f(self, x: int):
        return x

    class Dummy:
        pass

    try:
        typecheck(f, Dummy(), x="bad")
    except ValueError as e:
        assert "expected" in str(e)
    else:
        assert False, "typecheck did not raise"
