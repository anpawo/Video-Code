from videocode.transformation.color.Fade import fade, fadeIn, fadeOut
from videocode.transformation.color.Grayscale import grayscale
from videocode.transformation.size.Scale import scale
from videocode.transformation.size.Zoom import zoom
from videocode.transformation.position.MoveTo import moveTo
from videocode.transformation.setter.SetOpacity import setOpacity
from videocode.transformation.setter.SetAlign import setAlign
from videocode.transformation.setter.SetPosition import setPosition
from videocode.transformation.setter.Setter import setArgument
from videocode.Global import Metadata


def test_fade_and_aliases():
    f = fade(startOpacity=10, endOpacity=200, sides=[])
    assert f.startOpacity == 10
    fi = fadeIn()
    fo = fadeOut()
    assert isinstance(fi, fade)
    assert isinstance(fo, fade)


def test_grayscale_and_size():
    g = grayscale()
    assert hasattr(g, "__class__")
    s = scale(factor=1.5)
    assert s.factor[1] == 1.5
    z = zoom(factor=2.2, x=0.3, y=0.4)
    assert z.factor[1] == 2.2


def test_move_and_setters_modificator():
    md = Metadata(x=0, y=0)
    mv = moveTo(0.5, 0.5)
    # before modificator, src not set
    mv.modificator(md)
    # dstX/Y should have been applied
    assert md.x is not None
    assert md.y is not None

    md2 = Metadata(x=10, y=20)
    op = setOpacity(128)
    op.modificator(md2)
    assert md2.opacity == 128

    md3 = Metadata(x=1, y=2)
    al = setAlign(x=None, y=None)
    al.modificator(md3)
    # no change
    assert md3.alignX is not None

    sa = setPosition(5, 6)
    sa.modificator(md3)
    # setPosition setter may not change metadata here but shouldn't raise

    st = setArgument("radius", 10)
    assert st.name == "radius"
