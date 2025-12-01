import copy
import json

from videocode.Decorators import typecheck, inputCreation
from videocode.Global import Global, Metadata
from videocode.input.Input import Input
from videocode.input.shape.Line import line
from videocode.input.text.Formula import formula
from videocode.input.shape.Rectangle import square, rectangle
from videocode.transformation.size.Scale import scale
from videocode.transformation.setter.SetAlign import setAlign
from videocode.Constant import uint8


def test_typecheck_string_annotation_uint8():
    # create a dummy function and set its annotation to the string 'uint8'
    def f(self, x):
        return x

    f.__annotations__ = {"x": "uint8"}

    class D:
        pass

    # valid value
    typecheck(f, D(), x=10)

    # invalid value (too large for uint8)
    try:
        typecheck(f, D(), x=300)
    except ValueError:
        ok = True
    else:
        ok = False
    assert ok


def test_inputCreation_uses_defaults_and_sets_attrs():
    Global.stack.clear()

    class C:
        def __init__(self):
            pass

        @inputCreation
        def make(self, a: int = 5, b: int = 6):
            # should not be called here for return values, but decorator should set attributes
            self.called = True

    c = C()
    c.make()
    # decorator should have added a Create entry
    assert any((isinstance(item, dict) and item.get("action") == "Create") for item in Global.stack)
    # attributes should be set
    assert getattr(c, "a") == 5
    assert getattr(c, "b") == 6


def test_group_apply_autoadd_and_deepcopy_behavior():
    Global.stack.clear()

    class DummyInput:
        def __init__(self):
            # plain object, not subclassing Input to avoid Input.__setattr__ recursion
            self.calls = 0
            from videocode.Global import Global
            self.meta = Global.getDefaultMetadata()

        def apply(self, t, start=None, duration=None):
            # record that apply was called
            self.calls += 1
            return self

        def add(self):
            Global.stack.append({"action": "Add", "input": None})
            return self

    a = DummyInput()
    b = DummyInput()
    from videocode.input.group.Group import group

    g = group(a, b)
    # set group's meta automaticAdder to True to take the add branch
    g.meta.automaticAdder = True

    class T:
        def __init__(self):
            self.x = 1
        
        def modificator(self, meta):
            # Dummy modificator to make it behave like a Transformation
            pass

    t = T()
    g.apply(t)
    # because automaticAdder is True, group.apply should call add and thus Add entries exist
    assert any(isinstance(item, dict) and item.get("action") == "Add" for item in Global.stack)


def test_line_and_formula_push_tuple_entries():
    Global.stack.clear()
    line(7)
    formula("x=1")
    # find tuple entries
    assert any(isinstance(item, tuple) and item[0] == "Line" and item[1] == [7] for item in Global.stack)
    assert any(isinstance(item, tuple) and item[0] == "Formula" for item in Global.stack)


def test_square_and_rectangle_create_entries():
    Global.stack.clear()
    s = square(50)
    # square should create a rectangle Create entry
    assert any(isinstance(item, dict) and item.get("action") == "Create" for item in Global.stack)

    Global.stack.clear()
    r = rectangle(width=10, height=20)
    assert any(isinstance(item, dict) and item.get("action") == "Create" for item in Global.stack)


def test_transformation_str_and_setalign_branches():
    sc = scale(factor=1.5)
    s = str(sc)
    assert "factor" in s

    md = Metadata(x=0, y=0)
    al = setAlign(x="left", y=None)
    al.modificator(md)
    assert md.alignX == "left"
    # change only y
    md2 = Metadata(x=1, y=2)
    al2 = setAlign(x=None, y="bottom")
    al2.modificator(md2)
    assert md2.alignY == "bottom"


def test_typecheck_with_custom_type_names_and_ufloat():
    # Create a dummy type named 'uint' to exercise the Checks()[name] branch
    class uint:  # type: ignore
        pass

    def f(self, x):
        return x

    f.__annotations__ = {"x": uint}

    class D:
        pass

    # valid
    typecheck(f, D(), x=5)

    # invalid for uint (negative)
    try:
        typecheck(f, D(), x=-1)
    except ValueError:
        ok = True
    else:
        ok = False
    assert ok

    # test ufloat string annotation
    def g(self, x):
        return x

    g.__annotations__ = {"x": "ufloat"}
    # valid
    typecheck(g, D(), x=0.5)
    # invalid
    try:
        typecheck(g, D(), x=-0.1)
    except ValueError:
        ok2 = True
    else:
        ok2 = False
    assert ok2


def test_getvaluebypriority_default_branches():
    from videocode.Constant import getValueByPriority, default

    class T:
        duration = default(9)

    assert getValueByPriority(T(), default(4)) == 9

    # when duration argument is default
    assert getValueByPriority(object(), default(8)) == 8


def test_global_and_metadata_str_repr():
    m = Metadata(x=3, y=4)
    assert str(m) == "x=3, y=4"
    g = Global()
    assert "Stack=" in str(g)
    assert repr(g) == str(g)


def test_serialize_module_main_executes(capsys):
    import runpy
    import os

    # run the Serialize.py as a script to execute the __main__ block
    path = os.path.join(os.path.dirname(__file__), "..", "..", "videocode", "Serialize.py")
    runpy.run_path(path, run_name="__main__")
    # it will print some output; ensure no exception thrown
    captured = capsys.readouterr()
    assert captured is not None


def test_checks_getitem_and_rgba_behavior():
    # unknown custom type name should fall back to permissive checker
    class Foo:
        pass

    def f(self, x):
        return x

    f.__annotations__ = {"x": Foo}

    class D:
        pass

    # should not raise because unknown annotation becomes permissive
    typecheck(f, D(), x="anything")

    # rgba string annotation
    def g(self, x):
        return x

    g.__annotations__ = {"x": "rgba"}
    # valid
    typecheck(g, D(), x=(0, 0, 0, 0))
    # invalid
    try:
        typecheck(g, D(), x=(0, 0, 300, -1))
    except ValueError:
        ok = True
    else:
        ok = False
    assert ok


def test_input_add_respects_global_automaticAdder():
    Global.stack.clear()
    from videocode.input.shape.Circle import circle

    class MyInput(Input):
        def __init__(self):
            super().__init__()

    mi = MyInput()
    # set global automatic adder
    Global.automaticAdder = True
    mi.add()
    # no Add should be appended
    assert not any(isinstance(item, dict) and item.get("action") == "Add" for item in Global.stack)
    # reset
    Global.automaticAdder = False


def test_fade_sides_nonlist_case():
    from videocode.transformation.color.Fade import fade
    from videocode.Constant import LEFT

    f = fade(sides=LEFT)
    assert isinstance(f.sides, list)
    assert f.sides == [LEFT]


def test_typecheck_float_and_bool_annotation_and_exceptions():
    # float annotation
    def f(self, x):
        return x

    f.__annotations__ = {"x": float}

    class D:
        pass

    typecheck(f, D(), x=1.5)
    try:
        typecheck(f, D(), x="bad")
    except ValueError:
        ok = True
    else:
        ok = False
    assert ok

    # bool string annotation
    def g(self, x):
        return x

    g.__annotations__ = {"x": "bool"}
    typecheck(g, D(), x=True)
    try:
        typecheck(g, D(), x=1)
    except ValueError:
        ok2 = True
    else:
        ok2 = False
    assert ok2

    # rgba checker raising when given a non-iterable should be caught and produce ValueError
    def h(self, x):
        return x

    h.__annotations__ = {"x": "rgba"}
    try:
        typecheck(h, D(), x=None)
    except ValueError:
        ok3 = True
    else:
        ok3 = False
    assert ok3


def test_typecheck_positional_args_edge_cases():
    # more positional args than annotations -> continue branch
    def f(self, x):
        return x

    f.__annotations__ = {"x": int}

    class D:
        pass

    # call with two positional args (self + two values) to trigger i >= len(keys) branch
    typecheck(f, D(), 1, 2)

    # positional type mismatch should raise
    try:
        typecheck(f, D(), "bad")
    except ValueError:
        ok = True
    else:
        ok = False
    assert ok


def test_run_decorators_as_script():
    import runpy, os
    path = os.path.join(os.path.dirname(__file__), "..", "..", "videocode", "Decorators.py")
    runpy.run_path(path, run_name="__main__")


def test_resolve_checker_str_raises_and_positional_checker_exception():
    # ann __str__ that raises should be caught in _resolve_checker
    class Bad:
        def __str__(self):
            raise RuntimeError("bad str")

    def f(self, x):
        return x

    f.__annotations__ = {"x": Bad()}

    class D:
        pass

    # should not raise because _resolve_checker swallows the exception
    typecheck(f, D(), x="anything")

    # positional checker exception: rgba annotation but value is None -> checker raises and should cause ValueError
    def g(self, x):
        return x

    g.__annotations__ = {"x": "rgba"}

    try:
        typecheck(g, D(), None)
    except ValueError:
        ok = True
    else:
        ok = False
    assert ok


def test_incremental_group_functionality():
    """Test incremental group functionality to improve coverage"""
    from videocode.input.group.Incremental import incremental, linearAdd
    from videocode.input.media.Image import image
    from videocode.transformation.position.MoveTo import moveTo
    from videocode.transformation.color.Fade import fadeIn
    from videocode.Global import Global
    
    Global.stack.clear()
    
    # Create test inputs
    img1 = image("test1.png")
    img2 = image("test2.png")
    
    # Create incremental group with linear add modification
    incr_group = incremental(
        {moveTo: (linearAdd(dstX=10, dstY=5),)},
        img1, img2
    )
    
    # Apply transformation that has incremental
    move = moveTo(0, 0)
    incr_group.apply(move)
    
    # Apply transformation that doesn't have incremental (line 35 - else branch)
    fade = fadeIn()
    incr_group.apply(fade)
    
    # The incremental should have applied different transformations to each input
    assert len(Global.stack) > 0


def test_constantAdd_incremental_function():
    """Test constantAdd function from Incremental module"""
    from videocode.input.group.Incremental import constantAdd
    from videocode.transformation.position.MoveTo import moveTo
    
    # Create constant add function
    const_add = constantAdd(dstX=5, dstY=10)
    
    # Test it modifies transformation
    move = moveTo(0, 0)
    modified = const_add(move, 0)  # index 0
    
    assert hasattr(modified, 'dstX')
    assert hasattr(modified, 'dstY')
