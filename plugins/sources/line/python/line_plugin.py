from videocode.constants import WHITE
from videocode.input.shape.shape import Shape
from videocode.ty import rgba, wufloat
from videocode.utils.decorators import inputCreation


class line(Shape):
    @inputCreation
    def __init__(self, length: wufloat = 3, thickness: wufloat = 0.05, color: rgba = WHITE, rounded: bool = False):
        self.length = length
        self.thickness = thickness
        self.color = color
        self.rounded = rounded


def register(target):
    target["line"] = line
