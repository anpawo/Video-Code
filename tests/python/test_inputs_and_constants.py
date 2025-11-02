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
