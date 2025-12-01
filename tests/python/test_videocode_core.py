import inspect
import json
import tempfile
from pathlib import Path

import pytest

from videocode import VideoCode
from videocode.Global import Global, Metadata, wait, automaticAdderOn, automaticAdderOff
from videocode.Serialize import commentsToLabel, serializeScene
from videocode.Decorators import Checks, typecheck, inputCreation
from videocode.input.Input import Input
from videocode.transformation.setter.Setter import setArgument
from videocode.transformation.setter.SetPosition import setPosition
from videocode.transformation.setter.SetAlign import setAlign


def test_global_metadata_and_counters():
    # reset globals
    Global.stack.clear()
    Global.inputCounter = 0

    idx1 = Global.getIndex()
    idx2 = Global.getIndex()
    assert idx1 == 0
    assert idx2 == 1

    md = Global.getDefaultMetadata()
    assert isinstance(md, Metadata)
    # ensure copy
    md.x = 42
    md2 = Global.getDefaultMetadata()
    assert md2.x != 42

    wait(3)
    assert Global.stack[-1]["action"] == "Wait"

    automaticAdderOn()
    assert Global.automaticAdder is True
    automaticAdderOff()
    assert Global.automaticAdder is False


def test_comments_to_label_and_serialize_scene(tmp_path):
    # commentsToLabel
    s = "\n# Title\n# Next\ncontent"
    out = commentsToLabel(s)
    assert 'label("Title")' in out
    assert 'label("Next")' in out

    # serializeScene: create a small scene file that uses Global.wait
    scene = tmp_path / "scene.py"
    scene.write_text('from videocode.Global import wait\nwait(2)')

    Global.stack.clear()
    ser = serializeScene(str(scene))
    arr = json.loads(ser)
    assert any(item.get("action") == "Wait" for item in arr)


def test_checks_and_typecheck():
    c = Checks()
    assert c.uint(0)
    assert not c.uint(-1)
    assert c.uint8(255)
    assert not c.uint8(300)
    assert c.ufloat(0.5)
    assert not c.ufloat(-0.1)
    assert c.rgba((0, 128, 255))
    assert not c.rgba((0, -1, 256))
    assert c.bool(True)

    # typecheck should raise for mismatched types
    def f(self, x: int):
        return x

    class Dummy:
        pass

    with pytest.raises(ValueError):
        typecheck(f, Dummy(), x="not-an-int")


def test_input_and_transformations_behavior():
    Global.stack.clear()
    Global.inputCounter = 0

    class DummyInput(Input):
        def __init__(self):
            # call super implicitly sets index and meta
            super().__init__()

    # create dummy transformation-like object
    class DummyT:
        def __init__(self):
            self.foo = 1

        def modificator(self, meta):
            # modify metadata
            meta.x = 7

    di = DummyInput()
    assert di.add() is di
    assert Global.stack[-1]["action"] == "Add"

    di2 = DummyInput()
    di2.add()  # Test that add() method works
    assert Global.stack[-1]["action"] == "Add"

    t = DummyT()
    di.apply(t, start=0, duration=1)
    assert Global.stack[-1]["action"] == "Apply"

    # copy
    cp = di.copy()
    assert cp is not di
    assert Global.stack[-1]["action"] == "Create"

    # setPosition and setAlign proxies
    di.setPosition(10, 20)
    assert Global.stack[-1]["action"] == "Apply"
    di.setAlign(None, None)
    assert Global.stack[-1]["action"] == "Apply"

    # __setattr__ triggers setArgument when attribute exists
    di.some_attr = 123
    assert getattr(di, "some_attr") == 123


def test_input_creation_decorator_effects():
    Global.stack.clear()

    class MyInput(Input):
        def __init__(self):
            super().__init__()

        @inputCreation
        def create(self, filepath: str):
            # real init would do more; decorator should set attribute
            self.filepath = filepath

    mi = MyInput()
    mi.create("/tmp/x")
    # decorator should have created a Create action (it may be followed by Apply from setters)
    assert any(item.get("action") == "Create" for item in Global.stack)
    assert hasattr(mi, "filepath")
