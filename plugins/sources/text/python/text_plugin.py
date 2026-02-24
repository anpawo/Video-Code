from videocode.constants import WHITE
from videocode.input.input import Input
from videocode.ty import maybe, rgba, ufloat
from videocode.utils.decorators import inputCreation


class text(Input):
    @inputCreation
    def __init__(self, text: str, fontSize: ufloat = 3, color: rgba = WHITE, fontThickness: maybe[ufloat] = None):
        self.text = text
        self.fontSize = fontSize
        self.color = color
        self.fontThickness = fontThickness or fontSize * 2


def register(target):
    target["text"] = text
