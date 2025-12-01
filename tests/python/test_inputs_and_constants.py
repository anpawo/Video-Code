import copy
from videocode.Constant import *
from videocode.Global import Global, Metadata
from videocode.input.media.Video import video
from videocode.input.media.Image import image
from videocode.input.text.Text import text
from videocode.input.shape.Circle import circle
from videocode.input.shape.Rectangle import rectangle
from videocode.input.shape.Line import line
from videocode.input.group.Group import group


def test_constants_and_getvalue():
    # default values
    d = default(5)
    assert isinstance(d.defaultValue, int)

    class T:
        duration = 2

    assert getValueByPriority(T(), 1) == 2
    assert getValueByPriority(T(), default(3)) == 2

    class T2:
        duration = default(7)

    assert getValueByPriority(T2(), default(4)) == 7
    assert getValueByPriority(T2(), 6) == 6


def test_inputs_create_stack_entries():
    Global.stack.clear()

    v = video("/tmp/x.mp4")
    assert Global.stack[-1]["type"] == "Video"

    img = image("/tmp/x.png")
    assert Global.stack[-1]["type"] == "Image"

    t = text("hello", fontSize=2)
    assert Global.stack[-1]["type"] == "Text"

    c = circle(radius=10)
    # decorator adds Create (may not be the last entry because setters can append more actions)
    assert any(item.get("action") == "Create" for item in Global.stack)

    # Rectangle and Line exist as classes, instantiate them to ensure no runtime errors
    r = rectangle(10, 20)
    l = line(10)

    # group: group two inputs
    Global.stack.clear()
    g = group(v, img)
    g.add()
    # add should call add on children and push Add entries
    assert any(item.get("action") == "Add" for item in Global.stack)


def test_getValueByPriority_edge_cases():
    """Test edge cases for getValueByPriority to improve coverage"""
    from videocode.Constant import getValueByPriority, default
    
    # Test the else clause (line 77) - when neither has valid duration
    class InvalidObject:
        duration = "invalid"
    
    try:
        getValueByPriority(InvalidObject(), "also_invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected

    # Test the __str__ method of default (line 64)
    d = default(10)
    str_repr = str(d)
    assert "default(10)" in str_repr


def test_input_repr_and_autoAdd():
    """Test __repr__ method and autoAdd functionality to improve coverage"""
    from videocode.input.media.Image import image
    from videocode.transformation.position.MoveTo import moveTo
    from videocode.Global import Global
    
    Global.stack.clear()
    Global.automaticAdder = True
    
    # Test __repr__ method (line 157 in Input.py)
    img = image("test.png")
    repr_str = repr(img)
    assert "image" in repr_str
    
    # Test autoAdd functionality when Global.automaticAdder is True (line 84 in Input.py) 
    # The autoAdd decorator should add entries when Global.automaticAdder is True
    # Need to call apply() which has the @autoAdd decorator
    move = moveTo(10, 10)
    img.apply(move)
    assert any(item.get("action") == "Add" for item in Global.stack)
    
    Global.automaticAdder = False


def test_group_str_and_repr():
    """Test Group __str__ and __repr__ methods to improve coverage"""
    from videocode.input.group.Group import group
    from videocode.input.media.Image import image
    
    img1 = image("test1.png")
    img2 = image("test2.png")
    g = group(img1, img2)
    
    # Test __str__ method (line 64 in Group.py)
    str_repr = str(g)
    assert "image" in str_repr
    assert "pos=" in str_repr
    
    # Test __repr__ method (line 67 in Group.py)
    repr_str = repr(g)
    assert str_repr == repr_str


def test_transformation_repr():
    """Test Transformation __repr__ method to improve coverage"""
    from videocode.transformation.position.MoveTo import moveTo
    
    # Create a transformation and test __repr__ (line 36 in Transformation.py)
    move = moveTo(10, 20)
    repr_str = repr(move)
    assert "moveTo" in repr_str
